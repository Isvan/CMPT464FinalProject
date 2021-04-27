# CMPT 464 Final Project

# Technical details

## Setup
- Start a Virtual environment, you can run `python -m venv <path>`. It is suggested that you use the name following virtual* pattern.
For example, to create a venv in current directory, run `python -m venv .`
- Install all dependencies using `pip install -r requirements.txt`. We are using python 3.8 for this project.
- [REQUIRED] Download the given dataset: https://github.com/FENGGENYU/PartNet_symh and let it reside at `dataset/Chair`. Make sure that it's called exactly "Chair" and has `ops/ syms/` etc. folders within.
- [REQUIRED] Download current ML model to \ML\ourML\checkpoint\tripleView: https://drive.google.com/file/d/1txSLUsvMYqhLJafw8QQPWzpFRICXC0zy/view?usp=sharing
- [OPTIONAL] Download precalculated joints folder to \grass-master\Chair\models\joints: https://drive.google.com/drive/folders/1ZfgnWJKyDD8l28mHru_l7u5hr6zIbz5I?usp=sharing

## Extra
- Download final training data at https://drive.google.com/file/d/19w7n4ycMLvyRGky7xkI2eHFEkNHp4H6L/view?usp=sharing (not needed for execution)

## Running the main App
- To test on setA, setB and setC, make sure to run the app like this: `python3 MixAndMatchApp.py -setB -g 5 -p 50`. This will generate 50 chairs from set B and pick 5 best.
- If you want to test it on a random collection, make sure to run the app like this: `python3 MixAndMatchApp.py -r 10 -g 5 -p 50`. This will generate 50 chairs from random 10 and pick 5 best.

## Running the Viewer
- Run in the format of `python3 DatasetViewerApp.py n1 n2 n3...` to view/operate specified dataset meshes. E.g. `python3 DatasetViewerApp.py 2164 2165 2166 3452 5000`
- Run in the format of `python3 DatasetViewerApp.py -r X` to view/operate random X meshes from the dataset. E.g. `python3 DatasetViewerApp.py -r 10` will pick 10 random meshes and put them up.
- Run in the format of `python3 DatasetViewerApp.py -l` to run the latest input.
- Run in the format of `python3 DatasetViewerApp.py -setA` to run one of the given data sets.
- Press "a" and "d" to switch to prev/next models. Press "w" and "s" to look at particular parts of the model.
- Press "g" to generate a new chair. It's added in the end of all current models.
- Press "x" to take test depth screenshots of the chair present in the view. Saved to `screenshots/`
- Press "e" to evaluate the chair in the view. The score will appear in the caption on the top.
- Press "y" to save chair as "positive". Requires presence of `dataset/imageData/chairs-data/positive`
- Press "n" to save chair as "negative". Requires presence of `dataset/imageData/chairs-data/negative`

## Special considerations
- By default the app will save the split objs to disk in a new folder, this was done for easier loading but can cause hard storage usage to go to 2x the base set when ran on every chair
- The first time a chair is used it trys to find connecting vertices based on distance from other meshes, these are then saved to disk, this slows down generation a bit. uploaded to google drive to avoid generation if wanted (generated with current distance threshold of 0.025 in getJoints)
- If MixAndMatch is ran with a large amount of generated chairs(>100 for setC) compared to the input size there are some outliers that are bad but scored as good that may show up frequently near the top
-because of the above point the models are taken by generating 100 chairs from each set (aborting early if no new combinations are chosen for a number of selections)

## Guides

- To re-generate the `dataset/compiled` folder, ensure that there is `dataset/Chair` folder with all the dataset data within and run `dataset/json-compile.py` from within `dataset` folder.

# Non-technical details

## Roles

- **Iavor**: ML classificator
- **Maheep**: Mix and Matcher / Overall support
- **Greg**: Mix and Matcher
- **Vlad**: App maintenance / Overall support

## Team information

- General Project Meeting - every Wednesday, 7:00 pm - 8:30 pm

## Timeline (2021)

- **March 31st** - Project Inception
- **April 7th** - Have dataset viewer ready to go
- **April 14th** - Crude and basic parts replacement, baseline sorting/scoring of the chairs
- **April 21th** - Refined parts replacement, scorer to sort the models
- **April 26th, 12:30 pm** - Project defense and submission (submission deadline is at 11:45 pm).

## General Project Idea

- Parse input meshes, initialize their joints and form collection of parts
- Pick random parts from the collection and weld them together using their joints. Do this for N chairs.
- Screenshot each chair and assign the score based on the depth screenshot. Sort by the score.
- Export and display.

## Deliverables

### Dataset viewer (April 7th) - Done

- First milestone, this will require several other parts in the works
- Basic UX: "explore" the dataset, able to choose any provided mesh, able to look at the mesh and then look at each of the particular parts constituting the mesh
- Basic UI: one set of arrows to move between the meshes and another set of arrows to move between the parts in a particular mesh (or anything else simple and effective)
- Requires mesh-parts association which in turn requires dataset processing

### MVP (April 14th) - Done

- First working version of the project.

### Refined MVP (April 21st) - Done

- Decent general functionality. Proper scoring and mesh welding.
