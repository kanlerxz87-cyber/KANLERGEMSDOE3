import json
import tempfile
import unittest
from pathlib import Path
import sys
import numpy as np
import rasterio
from rasterio.transform import from_origin
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_rasters import overlap, validate
from build_site import build

class AuditTests(unittest.TestCase):
    def test_directional_overlap(self):
        a=np.zeros((20,20),bool); b=a.copy()
        a[5,5]=1; a[15,15]=1; b[5,5]=1
        self.assertEqual(overlap(a,b),.5)
        self.assertEqual(overlap(b,a),1.)
    def test_distance_boundary(self):
        a=np.zeros((10,10),bool); b=a.copy()
        a[2,2]=1; b[2,5]=1
        self.assertEqual(overlap(a,b),1.)
        b[:]=False; b[5,5]=1
        self.assertEqual(overlap(a,b),0.)
    def test_empty_not_unique(self):
        with self.assertRaises(ValueError): overlap(np.zeros((2,2),bool),np.zeros((2,2),bool))
    def test_invalid_values_and_grid(self):
        with tempfile.TemporaryDirectory() as d:
            ref=Path(d)/'ref.tif'; p=Path(d)/'pred.tif'
            profile=dict(driver='GTiff',width=3,height=3,count=1,dtype='float32',crs='EPSG:32611',transform=from_origin(0,300,100,100))
            def write(path,a,**extra):
                with rasterio.open(path,'w',**{**profile,**extra}) as ds: ds.write(a,1)
            a=np.zeros((3,3),dtype='float32');write(ref,a);write(p,a)
            self.assertTrue(validate(p,ref)['format_pass'])
            for value in [float('nan'),float('inf'),-0.01,1.01]:
                a[0,0]=value;write(p,a)
                self.assertFalse(validate(p,ref)['format_pass'])
            a[:]=0;write(p,a,transform=from_origin(1,300,100,100))
            self.assertFalse(validate(p,ref)['checks']['transform_match'])
            write(p,a,crs='EPSG:4326')
            self.assertFalse(validate(p,ref)['checks']['crs_match'])
    def test_outside_footprint_must_follow_template_mask(self):
        with tempfile.TemporaryDirectory() as d:
            ref=Path(d)/'ref.tif'; bad=Path(d)/'zeros-outside.tif'; good=Path(d)/'nodata-outside.tif'
            profile=dict(driver='GTiff',width=4,height=4,count=1,dtype='float32',crs='EPSG:32611',transform=from_origin(0,400,100,100),nodata=-9999.0)
            footprint=np.ones((4,4),dtype='float32');footprint[0,0]=-9999.0
            with rasterio.open(ref,'w',**profile) as ds:ds.write(footprint,1)
            zeros=np.zeros((4,4),dtype='float32')
            with rasterio.open(bad,'w',**{**profile,'nodata':None}) as ds:ds.write(zeros,1)
            accepted=zeros.copy();accepted[0,0]=-9999.0
            with rasterio.open(good,'w',**profile) as ds:ds.write(accepted,1)
            self.assertFalse(validate(bad,ref)['format_pass'])
            good_result=validate(good,ref)
            self.assertTrue(good_result['format_pass'])
            self.assertEqual(good_result['strict_template_validation']['valid_outside_footprint'],0)

    def test_report_fail_closed(self):
        root=Path(__file__).resolve().parents[1]
        j=json.loads((root/'docs/audit.json').read_text())
        self.assertEqual(len(j['rows']),9);self.assertEqual(len(j['pairs']),72)
        self.assertTrue(all(r['max_overlap_3px']>.7 and not r['unique_under_protocol'] for r in j['rows']))
        card=json.loads((root/'docs/run-card.json').read_text())
        self.assertEqual(card['verdict'],'negative')
        self.assertFalse(card.get('slot_authorized', False))
        note=card.get('submission_note') or card.get('note')
        self.assertIsInstance(note,str)
        self.assertLessEqual(len(note),140)
        if card['raster_sha256'] is not None:
            self.assertRegex(card['raster_sha256'], r'^[0-9a-f]{64}$')
        build()
        page=(root/'docs/index.html').read_text()
        self.assertIn('DO NOT SUBMIT',page)
        self.assertNotIn('download=',page)
        for link in ['review.md','hypotheses.md','audit.json','run-card.json','executive-summary.html']:
            self.assertTrue((root/'docs'/link).exists())

if __name__=='__main__': unittest.main()
