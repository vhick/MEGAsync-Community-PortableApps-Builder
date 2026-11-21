import importlib.util,pathlib,unittest
r=pathlib.Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('resolver',r/'scripts'/'resolve.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ResolverTest(unittest.TestCase):
 def test_numeric(self):
  a=[{'tag_name':x,'draft':False,'prerelease':False} for x in ['v6.9.1.0_Win','v6.10.0.0_Win','v6.11.0.0_Linux','v6.10.1.0_Win']]
  self.assertEqual(m.choose(a)['tag_name'],'v6.10.1.0_Win')
 def test_exclude_pre(self):
  a=[{'tag_name':'v7.0.0.0_Win','draft':False,'prerelease':True},{'tag_name':'v6.7.1.0_Win','draft':False,'prerelease':False}]
  self.assertEqual(m.choose(a)['tag_name'],'v6.7.1.0_Win')
  with self.assertRaises(ValueError):m.choose(a,'v7.0.0.0_Win')
if __name__=='__main__':unittest.main()
