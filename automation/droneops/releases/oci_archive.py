"""Prepare one pinned linux/amd64 cached image without changing payload bytes.

This build-side tool never contacts a registry or activates a container. The
result must still pass the platform bundle verifier before signing/import.
"""
import argparse
import hashlib
import io
import json
import os
import re
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

OCI='application/vnd.oci.image.manifest.v1+json'
DOCKER='application/vnd.docker.distribution.manifest.v2+json'
INDEXES={'application/vnd.oci.image.index.v1+json',
         'application/vnd.docker.distribution.manifest.list.v2+json'}
CONFIGS={'application/vnd.oci.image.config.v1+json','application/vnd.docker.container.image.v1+json'}
LAYERS={
    'application/vnd.docker.image.rootfs.diff.tar.gzip':'application/vnd.oci.image.layer.v1.tar+gzip',
    'application/vnd.docker.image.rootfs.diff.tar':'application/vnd.oci.image.layer.v1.tar',
    **{v:v for v in ('application/vnd.oci.image.layer.v1.tar','application/vnd.oci.image.layer.v1.tar+gzip',
                    'application/vnd.oci.image.layer.v1.tar+zstd')}}

class ArchiveError(ValueError):
    """Source identity, complete payload or target architecture is invalid."""

def _canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def _pairs(items):
    result={}
    for key,value in items:
        if key in result:raise ArchiveError('duplicate JSON key')
        result[key]=value
    return result

def normalize(source: Path,destination: Path,*,source_digest: str) -> dict:
    if destination.exists():raise ArchiveError('destination already exists')
    try:
        with tarfile.open(source,'r:') as archive:
            members={};seen=set()
            for member in archive:
                name=member.name.removeprefix('./')
                if (name in seen or name.startswith('/') or '..' in PurePosixPath(name).parts
                    or '\\' in name or not (member.isfile() or member.isdir())):
                    raise ArchiveError('unsafe or duplicate archive entry')
                seen.add(name)
                if len(seen)>100000:raise ArchiveError('too many archive entries')
                if member.isfile():
                    if name not in {'oci-layout','index.json'} and not re.fullmatch(r'blobs/sha256/[0-9a-f]{64}',name):
                        raise ArchiveError('unexpected archive entry')
                    members[name]=member
            def small(name):
                member=members[name]
                if member.size>4*1024*1024:raise ArchiveError('oversized JSON metadata')
                return archive.extractfile(member).read()
            def data(name):return json.loads(small(name),object_pairs_hook=_pairs)
            if data('oci-layout')!={'imageLayoutVersion':'1.0.0'}:raise ArchiveError('invalid OCI layout')
            index=data('index.json')
            if index.get('schemaVersion')!=2 or len(index.get('manifests',[]))!=1:
                raise ArchiveError('one pinned source is required')
            root=index['manifests'][0]
            if root.get('digest')!=source_digest:raise ArchiveError('source digest differs')
            verified={}
            def blob(desc,types):
                digest=desc.get('digest')
                if (not isinstance(digest,str) or not re.fullmatch(r'sha256:[0-9a-f]{64}',digest)
                    or desc.get('mediaType') not in types or 'urls' in desc
                    or type(desc.get('size')) is not int or desc['size']<1):
                    raise ArchiveError('invalid content descriptor')
                name='blobs/sha256/'+digest[7:]
                member=members[name]
                if member.size!=desc['size']:raise ArchiveError('content size differs')
                if digest not in verified:
                    with archive.extractfile(member) as stream:
                        if hashlib.file_digest(stream,'sha256').hexdigest()!=digest[7:]:
                            raise ArchiveError('content digest differs')
                    verified[digest]=member
                return name
            selected=root
            for _ in range(5):
                name=blob(selected,INDEXES|{OCI,DOCKER})
                manifest=data(name)
                if manifest.get('schemaVersion')!=2:raise ArchiveError('invalid manifest schema')
                if selected['mediaType'] not in INDEXES:break
                matches=[d for d in manifest.get('manifests',[]) if d.get('platform',{}).get('os')=='linux'
                         and d.get('platform',{}).get('architecture')=='amd64']
                if len(matches)!=1:raise ArchiveError('ambiguous or unavailable linux/amd64 image')
                selected=matches[0]
            else:raise ArchiveError('nested indexes exceed limit')
            config=manifest['config'];layers=manifest['layers']
            if not isinstance(layers,list) or not layers:raise ArchiveError('empty layers')
            configuration=data(blob(config,CONFIGS))
            if configuration.get('os')!='linux' or configuration.get('architecture')!='amd64':
                raise ArchiveError('configuration architecture differs')
            for layer in layers:blob(layer,set(LAYERS))
            original=small(name)
            if (selected['mediaType']==OCI and config['mediaType']=='application/vnd.oci.image.config.v1+json'
                and all(layer['mediaType'].startswith('application/vnd.oci.') for layer in layers)):
                output_manifest=original
            else:
                converted={**manifest,'mediaType':OCI,
                           'config':{**config,'mediaType':'application/vnd.oci.image.config.v1+json'},
                           'layers':[{**layer,'mediaType':LAYERS[layer['mediaType']]} for layer in layers]}
                output_manifest=_canonical(converted)
            digest='sha256:'+hashlib.sha256(output_manifest).hexdigest()
            output_index={'schemaVersion':2,'manifests':[{'mediaType':OCI,'digest':digest,
                'size':len(output_manifest),'annotations':{'org.opencontainers.image.ref.name':'appliance'}}]}
            payloads={desc['digest']:verified[desc['digest']] for desc in [config,*layers]}
            with tempfile.TemporaryDirectory(prefix='bs01-oci-',dir=destination.parent) as folder:
                temporary=Path(folder)/'image.tar'
                with tarfile.open(temporary,'w') as output:
                    def add(name,content):
                        member=tarfile.TarInfo(name);member.size=len(content);member.mode=0o644
                        output.addfile(member,io.BytesIO(content))
                    add('oci-layout',b'{"imageLayoutVersion":"1.0.0"}')
                    add('index.json',_canonical(output_index))
                    add('blobs/sha256/'+digest[7:],output_manifest)
                    for key,member in sorted(payloads.items()):
                        copied=tarfile.TarInfo('blobs/sha256/'+key[7:]);copied.size=member.size;copied.mode=0o644
                        with archive.extractfile(member) as stream:output.addfile(copied,stream)
                os.link(temporary,destination)
            return {'source_digest':source_digest,'selected_source_digest':selected['digest'],
                    'digest':digest,'config_digest':config['digest'],
                    'layer_digests':[layer['digest'] for layer in layers]}
    except ArchiveError:raise
    except (OSError,tarfile.TarError,KeyError,TypeError,ValueError,AttributeError) as exc:
        raise ArchiveError('invalid or incomplete image archive') from exc

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('destination',type=Path)
    parser.add_argument('--source-digest',required=True)
    args=parser.parse_args()
    print(json.dumps(normalize(args.source,args.destination,source_digest=args.source_digest),sort_keys=True))
