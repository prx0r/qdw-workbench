from pathlib import Path
import tempfile,shutil,subprocess,sys
R=Path(__file__).resolve().parents[1]
def must_fail_mutation(path,old,new,needle):
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'repo'; shutil.copytree(R,d,ignore=shutil.ignore_patterns('target','node_modules','.venv','build'))
        p=d/path; txt=p.read_text(); assert old in txt, f"mutation anchor missing {path}"; p.write_text(txt.replace(old,new,1))
        cp=subprocess.run([sys.executable,str(d/'tests/validate_structure.py')],cwd=d,text=True,capture_output=True)
        if cp.returncode==0: raise AssertionError(f"checker survived forbidden mutation {needle}")
        print('MUTATION KILLED:',needle)
must_fail_mutation('crates/qdw-node/src/config.rs','127.0.0.1:9902','0.0.0.0:9902','public node bind')
must_fail_mutation('integrations/qdw_bridge/src/qdw_workbench_bridge/app.py','from qdw.system import QDWSystem','from qdw.system import SomethingElse','detached authority')
print('MUTATION HARNESS PASS')
