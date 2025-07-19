import os
import subprocess
import argparse
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

def run_script(script):
    try:
        logging.info(f"Running {script}...")
        subprocess.run(["python", script], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running {script}: {e}")

def main(scripts):
    for script in scripts:
        run_script(script)

if __name__ == "__main__":
    setup_logging()

    parser = argparse.ArgumentParser(description="Run project scripts.")
    parser.add_argument(
        "--scripts",
        nargs="*",
        default=[
            "data_processing/data_cleaner.py",
            "data_processing/chunker.py",
            "pinecone_db/pinecone_setup.py",
            "pinecone_db/embeddings.py",
            "app.py",
        ],
        help="List of scripts to run.",
    )

    args = parser.parse_args()
    main(args.scripts)
