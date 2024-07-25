# Author 2024, Tanaya Balthazar (tbalthaz)

DOCUMENTATION = '''

---
Description: Encapsulates the functionality to create a virtual environment, 
install requirements, configure the environment, and manage AI models for possible future 
AI integration.

Requirements:
 
- A requirements.txt file listing all the Python packages required for your AI project. 
This file needs to ensure each line contains a package name and optionally a version specifier:

numpy==1.21.0
pandas>=1.3.0
scikit-learn
tensorflow

- A JSON configuration file that specifies various settings for your AI environment or models.
{
  "model_path": "models/",
  "data_path": "data/",
  "learning_rate": 0.001,
  "batch_size": 32
}

- Model files to load or save models

---

EXAMPLE:

- name: Set up AI environment
  hosts: localhost
  tasks:
    - name: Create AI environment
      command: >
        python3 ai_environment.py --env_name my_ai_env --requirements_file requirements.txt --action create
  - name: Install Requirements
      command: >
        python3 /path/to/ai_environment.py --env_name my_ai_env --requirements_file /path/to/requirements.txt --action install
      when: install_reqs is defined and install_reqs

    - name: Configure Environment
      command: >
        python3 /path/to/ai_environment.py --env_name my_ai_env --config_file /path/to/config.json --action configure
      when: configure_env is defined and configure_env

    - name: Manage Models (Load)
      command: >
        python3 /path/to/ai_environment.py --env_name my_ai_env --action manage --model_action load --model_name my_model
      when: load_model is defined and load_model

    - name: Manage Models (Save)
      command: >
        python3 /path/to/ai_environment.py --env_name my_ai_env --action manage --model_action save --model_name my_model
      when: save_model is defined and save_model        

ansible-playbook -i localhost, manage_ai_environments.yml

'''



import subprocess  # Import the subprocess module for running new applications or programs through Python code
import os  # Import the os module for interacting with the operating system
import json  # Import the json module for working with JSON data

class AIEnvironment:
    def __init__(self, env_name, requirements_file=None, config_file=None):
        """
        Initialize the AIEnvironment class with environment name, requirements file, and config file.
        """
        self.env_name = env_name  # Store the environment name
        self.requirements_file = requirements_file  # Store the path to the requirements file
        self.config_file = config_file  # Store the path to the configuration file

    def create_environment(self):
        """
        Create a virtual environment using Python's venv module.
        """
        try:
            subprocess.check_call(['python3', '-m', 'venv', self.env_name])  # Create the virtual environment
            print(f"Virtual environment '{self.env_name}' created successfully.")  # Print success message
        except subprocess.CalledProcessError as e:  # Catch any errors
            print(f"Failed to create virtual environment: {e}")  # Print error message
            raise  # Re-raise the exception

    def install_requirements(self):
        """
        Install packages from a requirements file into the virtual environment.
        """
        if self.requirements_file:  # Check if a requirements file is provided
            try:
                subprocess.check_call([f'{self.env_name}/bin/pip', 'install', '-r', self.requirements_file])  # Install requirements
                print(f"Requirements from '{self.requirements_file}' installed successfully.")  # Print success message
            except subprocess.CalledProcessError as e:  # Catch any errors
                print(f"Failed to install requirements: {e}")  # Print error message
                raise  # Re-raise the exception

    def configure_environment(self):
        """
        Apply configurations from a JSON configuration file.
        """
        if self.config_file:  # Check if a config file is provided
            try:
                with open(self.config_file, 'r') as file:  # Open the config file
                    config = json.load(file)  # Load the JSON data
                # Apply configurations (this is a placeholder for actual configuration logic)
                print(f"Configurations from '{self.config_file}' applied successfully.")  # Print success message
            except json.JSONDecodeError as e:  # Catch JSON decode errors
                print(f"Failed to parse configuration file: {e}")  # Print error message
                raise  # Re-raise the exception
            except IOError as e:  # Catch IO errors
                print(f"Failed to read configuration file: {e}")  # Print error message
                raise  # Re-raise the exception

    def manage_models(self, action, model_name):
        """
        Manage AI models (load or save).
        """
        # Placeholder for model management logic
        if action == 'load':  # Check if the action is to load a model
            print(f"Loading model '{model_name}'...")  # Print loading message
            # Load model logic here
        elif action == 'save':  # Check if the action is to save a model
            print(f"Saving model '{model_name}'...")  # Print saving message
            # Save model logic here
        else:  # If the action is unknown
            print(f"Unknown action '{action}' for model management.")  # Print error message

def main():
    """
    Main function to parse arguments and manage AI environments.
    """
    import argparse  # Import the argparse module for command-line argument parsing

    parser = argparse.ArgumentParser(description='Manage AI environments with Ansible.')  # Create argument parser
    parser.add_argument('--env_name', required=True, help='Name of the environment')  # Add environment name argument
    parser.add_argument('--requirements_file', help='Path to the requirements file')  # Add requirements file argument
    parser.add_argument('--config_file', help='Path to the configuration file')  # Add config file argument
    parser.add_argument('--action', choices=['create', 'install', 'configure', 'manage'], help='Action to perform')  # Add action argument
    parser.add_argument('--model_action', choices=['load', 'save'], help='Model management action')  # Add model action argument
    parser.add_argument('--model_name', help='Name of the model')  # Add model name argument

    args = parser.parse_args()  # Parse the command-line arguments

    ai_env = AIEnvironment(args.env_name, args.requirements_file, args.config_file)  # Create an instance of AIEnvironment

    if args.action == 'create':  # Check if the action is to create an environment
        ai_env.create_environment()  # Call the create_environment method
    elif args.action == 'install':  # Check if the action is to install requirements
        ai_env.install_requirements()  # Call the install_requirements method
    elif args.action == 'configure':  # Check if the action is to configure the environment
        ai_env.configure_environment()  # Call the configure_environment method
    elif args.action == 'manage':  # Check if the action is to manage models
        if args.model_action and args.model_name:  # Check if model action and name are provided
            ai_env.manage_models(args.model_action, args.model_name)  # Call the manage_models method
        else:  # If model action or name are missing
            print("Model action and name are required for management.")  # Print error message
    else:  # If no valid action is specified
        print("No valid action specified.")  # Print error message

if __name__ == '__main__':
    main()  # Call the main function if the script is run directly
