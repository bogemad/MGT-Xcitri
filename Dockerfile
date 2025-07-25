# syntax=docker/dockerfile:1

####################################
# 1. Base image with conda         #
####################################
FROM continuumio/miniconda3:latest

####################################
# 2. Create & switch to app dir    #
####################################
WORKDIR /app

####################################
# 3. Install Postgres client tools #
####################################
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      postgresql-client \
      openssh-client \
 && rm -rf /var/lib/apt/lists/*

####################################
# 4. Copy & build your conda env   #
####################################
COPY setup/mgt_conda_env.yaml environment.yml
RUN conda env create -f environment.yml \
 && conda clean -afy

####################################
# 5. Use your conda env for RUNs   #
####################################
SHELL ["conda", "run", "-n", "mgtenv", "/bin/bash", "-lc"]

####################################
# 6. Copy in the rest of the code  #
####################################
COPY . /app


####################################
# 7. Expose Django’s port          #
####################################
EXPOSE 8000

####################################
# 8. Fallback CMD                   #
#    (Compose will override via   #
#     its `entrypoint:`)           #
####################################
CMD ["bash", "-lc", "python manage.py runserver 0.0.0.0:8000 --settings Mgt.settings_template"]
