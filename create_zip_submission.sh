#!/bin/bash

# Function to check if a field is empty
check_field() {
  if [ -z "$1" ]; then
    echo "Error: $2 is not specified in team_info.yml. Generation of the submission ZIP file is not possible."
    exit 1
  fi
}

# Check if requirements.txt exists
if [ ! -f requirements.txt ]; then
  echo "Warning: requirements.txt not found in this directory. Generation of the submission ZIP file is not possible."
  exit 1
fi

# Check if my_drone_eval.py exists
if [ ! -f src/swarm_rescue/solutions/my_drone_eval.py ]; then
  echo "Warning: my_drone_eval.py not found in src/swarm_rescue/solutions directory."
  exit 1
fi

# Check if team_info.yml exists
if [ ! -f src/swarm_rescue/solutions/team_info.yml ]; then
  echo "Warning: team_info.yml not found in src/swarm_rescue/solutions directory. Generation of the submission ZIP file is not possible."
  exit 1
fi

# Extract the team_number, team_name, and team_members from team_info.yml
team_number=$(grep 'team_number:' src/swarm_rescue/solutions/team_info.yml | awk '{print $2}')
team_name=$(grep 'team_name:' src/swarm_rescue/solutions/team_info.yml | awk '{print $2}')
team_members=$(grep 'team_members:' src/swarm_rescue/solutions/team_info.yml | awk -F': ' '{print $2}')

# Format the team number with leading zeros if necessary
formatted_team_number=$(printf "%02d" $team_number)

# Validate the extracted fields
check_field "$team_name" "Team name"
check_field "$team_members" "Team members"

# Display the extracted information and ask for confirmation
echo "Team number: $formatted_team_number"
echo "Team name: $team_name"
echo "Team members: $team_members"
echo "Do you confirm this information? (y/n)"
read confirmation

if [ "$confirmation" != "y" ]; then
  echo "Please modify your team_info.yml file to correct the information and try again. Generation of the submission ZIP file is not possible."
  exit 1
fi

# Ask the user to choose an evaluation step
echo "Please choose an evaluation step from the following options (a, b, or c):"
echo "a) intermediate01"
echo "b) intermediate02"
echo "c) final"
read evalstep_choice

# Set the evaluation step based on user input
case $evalstep_choice in
  a)
    evalstep="intermediate01"
    ;;
  b)
    evalstep="intermediate02"
    ;;
  c)
    evalstep="final"
    ;;
  *)
    echo "Invalid choice. Generation of the submission ZIP file is not possible."
    exit 1
    ;;
esac

# Define the zip file name
zip_file="team${formatted_team_number}_${evalstep}.zip"

# Check if the zip file already exists and delete it if it does
if [ -f "$zip_file" ]; then
  echo
  echo "File $zip_file already exists. Deleting the existing zip file."
  rm "$zip_file"
fi

# Create the zip file with the specified team number and chosen eval step
echo
echo "Create the ZIP file $zip_file:"
if ! (cd src/swarm_rescue/solutions && zip -r ../../../"$zip_file" .); then
  echo "Error: Failed to create the ZIP file. Generation of the submission ZIP file is not possible."
  exit 1
fi

# Update the zip file to include requirements.txt
if ! zip -u "$zip_file" requirements.txt; then
  echo "Error: Failed to update the ZIP file with requirements.txt. Generation of the submission ZIP file is not possible."
  exit 1
fi

# Prompt the user to send the zip file to their evaluator
echo
echo "Please send the file $zip_file to your evaluator."
