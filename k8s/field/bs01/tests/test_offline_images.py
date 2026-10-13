import json,re,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
class OfflineImages(unittest.TestCase):
    def test_exact_repository_policy_keeps_other_images_verified(self):
        path=ROOT/'k8s/field/bs01/updater/90-droneops-offline-images.conf'
        policy=json.loads(path.read_text())
        self.assertEqual(set(policy),{'apiVersion','kind','imagePullCredentialsVerificationPolicy','preloadedImagesVerificationAllowlist'})
        self.assertEqual(policy['apiVersion'],'kubelet.config.k8s.io/v1beta1')
        self.assertEqual(policy['kind'],'KubeletConfiguration')
        self.assertEqual(policy['imagePullCredentialsVerificationPolicy'],'NeverVerifyAllowlistedImages')
        images=policy['preloadedImagesVerificationAllowlist']
        self.assertEqual(len(images),35)
        self.assertEqual(images,sorted(set(images)))
        for image in images:
            self.assertRegex(image,r'^[a-z0-9.:-]+/[a-z0-9/_-]+$')
            self.assertNotIn('*',image)
            self.assertNotIn('@',image)
        private={i.removeprefix('192.168.1.15:5000/lab/droneops-platform/') for i in images if i.startswith('192.168.1.15:5000/')}
        self.assertEqual(private,{'web','simulator','vehicle-gateway','mission-control','fleet-coordination','db-migrations','martin','droneops-raster'})
        self.assertIn('docker.io/rancher/mirrored-pause',images)
        self.assertNotIn('192.168.1.15:5000',images)

if __name__=='__main__':unittest.main()
