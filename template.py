import os
from pathlib import Path
import logging

#what are the other parameter options, what does this one do
logging.basicConfig(level=logging.INFO, format='[%(asctime)s]:%(message)s')

project_name = "Factline"

file_list = [
    ".github/workflows/.gitkeep", #Github Actions
    ".gitignore",
    ".env",
    f"src/{project_name}/__init__.py", #make custom errors
    f"src/{project_name}/components/__init__.py", #Different steps of pipeline
    f"src/{project_name}/utils/__init__.py",
    f"src/{project_name}/utils/common.py", #Repetitve functions, like get_headers() to get browser headers
    f"src/{project_name}/config/__init__.py",
    f"src/{project_name}/config/configuration.py", #constant parts of the components, system prompts etc
    f"src/{project_name}/pipeline/__init__.py",
    f"src/{project_name}/entity/__init__.py",
    f"src/{project_name}/entity/config_entity.py", #if can breakdown in datastructures, or model configurtions and all 
    f"src/{project_name}/constants/__init__.py",
    "config/config.yaml",
    "main.py", #call the pipeline
    "app.py", #Streamlit frontend to track project
    "Dockerfile",
    "requirements.txt",
    "templates/index.html" #use this or streamlit to store videologs, if possible make dynamic so no need of yt studio
    ]

for i in file_list:
    path = Path(i)
    fdir, fname = os.path.split(path)

    if fdir != "":
        os.makedirs(fdir, exist_ok=True)
        logging.info(f"Creating directory: {fdir} for the file {fname}")

    if (not os.path.exists(path)) or (os.path.getsize(path) == 0):
        with open(path,"w") as f:
            pass
        logging.info(f"Creating empty file :{path}")
    else:
        logging.info(f"{fname} already exists")