import importlib.util,pathlib,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('patch',ROOT/'scripts'/'patch_source.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PatchTests(unittest.TestCase):
 def test_exact_anchor(self):
  with tempfile.TemporaryDirectory() as tmp:
   target=pathlib.Path(tmp)/m.TARGET;target.parent.mkdir(parents=True)
   original='void MegaApplication::loadDataPath()\n{\n    Platform::getInstance()->createFolderRestrictedToOwner(dataPath, &dataPathCreationError);\n'+m.NEEDLE+'\n}'
   target.write_text(original,encoding='utf-8');m.patch(pathlib.Path(tmp))
   result=target.read_text();self.assertIn('MEGA_PORTABLE_DATA_DIR',result);self.assertEqual(result.count(m.NEEDLE),1)
   with self.assertRaises(SystemExit):m.patch(pathlib.Path(tmp))
 def test_fail_closed(self):
  with tempfile.TemporaryDirectory() as tmp:
   target=pathlib.Path(tmp)/m.TARGET;target.parent.mkdir(parents=True);target.write_text('changed upstream',encoding='utf-8')
   with self.assertRaises(SystemExit):m.patch(pathlib.Path(tmp))
if __name__=='__main__':unittest.main()
