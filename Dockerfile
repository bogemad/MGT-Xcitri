# 1. Base image with conda
FROM continuumio/miniconda3:latest

# 2. Set a working directory
WORKDIR /app

# 3. Copy & build the conda environment
COPY setup/mgt_conda_env.yaml environment.yml
RUN conda env create -f environment.yml \
    && conda clean -afy

# 4. Switch default shell into the new env
SHELL ["conda", "run", "-n", "mgtenv", "/bin/bash", "-c"]

# 5. Copy the rest of your code
COPY . /app

# 6. Rename settings_template.py to settings.py
#    so Django picks it up as the default settings module
RUN cp Mgt/Mgt/settings_template.py Mgt/Mgt/settings.py

# 7. Collect static assets
WORKDIR /app/setup
RUN ./setup_new_database.ssh Xcitri_inputs.setupPath

# 8. Expose the port your app listens on
EXPOSE 8000

# 9. Run Gunicorn using your conda env
CMD ["gunicorn", "Mgt.wsgi:application", "--bind", "0.0.0.0:8000"]
