# Code Submission Guidelines

In order for your code to be evaluated smoothly, each participant must adhere to the following rules.

Below, *evalstep* refers to:
- *intermediate01*, for the first intermediate evaluation.
- *intermediate02*, for the second intermediate evaluation.
- *final*, for the final evaluation.

## Cleaning your code

To ensure clarity and avoid unnecessary debugging information:
* **Disable** as many console displays (print(...)) as possible.
* **Hide or disable** debugging tools (e.g., OpenCV windows).
* **Verify** that not forbidden functions or data (e.g., noiseless position information) are used.

## Verification Before Submission

Test your solution thoroughly to ensure:
* It works **without your local modifications** when using a clean installation of the *swarm_rescue* project.
* Your code does not **crash unexpectedly or enter an infinite loop**, especially when drones cross **special zones** (e.g., no-com zone, no-GPS zone, or killing zone).

## Directory and File Naming

The code to submit should only include the direct content of your "solutions" folder. 
Place your code in a directory named *teamXX_evalstep*, where XX corresponds to your team number (e.g., team05_intermediate01 for Team 5, first intermediate evaluation).

## Required Files

Your submission must include the following files:
* *my_drone_eval.py*: replace ```your_drone_class_name``` by your drone class name.
```Python
class MyDroneEval(your_drone_class_name):
    pass
```
* *team_info.yml*: ensure all fields are correctly completed, especially *team_number* and *team_members*.
* *requirements.txt*: This file must include both the original and any additional Python dependencies, and it should be located at the root of your project.

## Exclusions

Do not include the following:
* The entire *swarm_rescue* directory.
* The *.venv* directory, which contains the virtual environment and can be very large (~1GB).

## Submission Process

1. Compress the teamXX_evalstep directory (e.g., teamXX_intermediate01, teamXX_intermediate02, or teamXX_final) into a .zip file.
2. Ensure the resulting file is **lightweight** (a few KB).
3. Send the **zipped file** to your evaluator (emmanuel.battesti@ensta.fr for french participants)
4. Use the following format in the **email subject**: *teamXX_evalstep* (replace XX with your team number and *evalstep* with the evaluation step name).

## ZIP File Generation Script for Submissions

If you are using Linux, the easier way to create the submission file is to use a script called *create_zip_submission.sh*.

This script is designed to facilitate the creation and submission of ZIP files containing your team's solutions for the "Swarm Rescue" project. It automates the process of checking necessary files, validating team information, and generating the final ZIP file, ensuring the accuracy and completeness of the provided data.

### Usage
To use this script *create_zip_submission.sh*, follow these steps:
* If not already done, make the script executable using the command: ```chmod +x create_zip_submission.sh```.
* Run the script: ```./create_zip_submission.sh.```
* Follow the on-screen instructions to confirm team information and choose the evaluation step.
* Once the ZIP file is generated, send it to your evaluator as instructed.
* This script is designed to ensure a smooth and error-free submission of your solutions. 