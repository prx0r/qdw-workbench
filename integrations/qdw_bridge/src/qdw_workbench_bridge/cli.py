def main():
    import argparse,uvicorn
    p=argparse.ArgumentParser();p.add_argument("--listen",default="127.0.0.1:9911");a=p.parse_args();host,port=a.listen.rsplit(":",1);uvicorn.run("qdw_workbench_bridge.app:app",host=host,port=int(port),log_level="info")
if __name__=="__main__":main()
