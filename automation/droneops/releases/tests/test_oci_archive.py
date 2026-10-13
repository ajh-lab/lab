import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from automation.droneops.releases.oci_archive import normalize, ArchiveError

DOCKER='application/vnd.docker.distribution.manifest.v2+json'
OCI='application/vnd.oci.image.manifest.v1+json'
def encoded(data):return json.dumps(data,sort_keys=True,separators=(',',':')).encode()
def fixture(path,*,ambiguous=False,corrupt=False,architecture='amd64'):
    blobs={}
    def blob(data,media):
        digest='sha256:'+hashlib.sha256(data).hexdigest()
        blobs['blobs/sha256/'+digest[7:]]=data
        return {'digest':digest,'size':len(data),'mediaType':media}
    config=blob(encoded({'architecture':architecture,'os':'linux','config':{'Cmd':['app']},
                         'moby.buildkit.buildinfo.v1':'fixture-build-metadata'}),'application/vnd.docker.container.image.v1+json')
    layer=blob(b'layer-payload','application/vnd.docker.image.rootfs.diff.tar.gzip')
    manifest=blob(encoded({'schemaVersion':2,'mediaType':DOCKER,'config':config,'layers':[layer]}),DOCKER)
    child={**manifest,'platform':{'os':'linux','architecture':'amd64'}}
    root=blob(encoded({'schemaVersion':2,'manifests':[child]* (2 if ambiguous else 1)}),
              'application/vnd.docker.distribution.manifest.list.v2+json')
    if corrupt:blobs['blobs/sha256/'+layer['digest'][7:]]=b'bad-layer-data'
    with tarfile.open(path,'w') as archive:
        for name,data in {'oci-layout':b'{"imageLayoutVersion":"1.0.0"}',
                          'index.json':encoded({'schemaVersion':2,'manifests':[root]}),**blobs}.items():
            member=tarfile.TarInfo(name);member.size=len(data);archive.addfile(member,io.BytesIO(data))
    return root['digest'],config,layer


class ArchiveTests(unittest.TestCase):
    def test_conversion_preserves_payload_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source.tar'
            digest,config,layer=fixture(source)
            first=normalize(source,root/'one.tar',source_digest=digest)
            second=normalize(source,root/'two.tar',source_digest=digest)
            self.assertEqual(first,second)
            self.assertEqual((root/'one.tar').read_bytes(),(root/'two.tar').read_bytes())
            self.assertEqual(first['config_digest'],config['digest'])
            self.assertEqual(first['layer_digests'],[layer['digest']])
            native=normalize(root/'one.tar',root/'three.tar',source_digest=first['digest'])
            self.assertEqual(native['digest'],first['digest'])
            self.assertEqual((root/'one.tar').read_bytes(),(root/'three.tar').read_bytes())
            with tarfile.open(root/'one.tar') as archive:
                index=json.load(archive.extractfile('index.json'))
                self.assertEqual(index['manifests'][0]['mediaType'],OCI)
                manifest=json.load(archive.extractfile('blobs/sha256/'+first['digest'][7:]))
                self.assertEqual(manifest['config']['digest'],config['digest'])
                preserved=json.load(archive.extractfile('blobs/sha256/'+config['digest'][7:]))
                self.assertIn('moby.buildkit.buildinfo.v1',preserved)
            with self.assertRaises(ArchiveError):
                normalize(source,root/'one.tar',source_digest=digest)

    def test_rejects_invalid_source_before_publication(self):
        for options in ({'ambiguous':True},{'corrupt':True},{'architecture':'arm64'}):
            with self.subTest(options=options),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);source=root/'source.tar';dest=root/'result.tar'
                digest,_,_=fixture(source,**options)
                with self.assertRaises(ArchiveError):normalize(source,dest,source_digest=digest)
                self.assertFalse(dest.exists())
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source.tar';fixture(source)
            with self.assertRaises(ArchiveError):normalize(source,root/'result.tar',source_digest='sha256:'+'0'*64)

    def test_rejects_archive_links_and_duplicate_paths(self):
        for attack in ('link','duplicate','traversal'):
            with self.subTest(attack=attack),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);source=root/'source.tar';digest,_,_=fixture(source)
                with tarfile.open(source,'a') as archive:
                    item=tarfile.TarInfo('index.json' if attack=='duplicate' else '../escape' if attack=='traversal' else 'link')
                    if attack=='link':item.type=tarfile.SYMTYPE;item.linkname='/etc/passwd'
                    archive.addfile(item,io.BytesIO())
                with self.assertRaises(ArchiveError):normalize(source,root/'result.tar',source_digest=digest)


if __name__=='__main__':unittest.main()
