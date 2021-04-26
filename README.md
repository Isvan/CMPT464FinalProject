# CMPT 464 Final Project

# Technical details

## How to install
- Start a Virtual environment, you can run `python -m venv <path>`. For example, to create a venv in current directory, run `python -m venv .`
- Install all dependencies using `pip install -r requirements.txt`. We are using python 3.8 for this project.

## Running

- Run in the format of `python3 DatasetViewerApp.py n1 n2 n3...` to view/operate specified dataset meshes. E.g. `python3 DatasetViewerApp.py 2164 2165 2166 3452 5000`
- Run in the format of `python3 DatasetViewerApp.py -r X` to view/operate random X meshes from the dataset. E.g. `python3 DatasetViewerApp.py -r 10` will pick 10 random meshes and put them up.
- Press "x" to take test depth screenshots of the chair present in the view. Saved to `screenshots/`
- Press "g" to generate a new chair. It's added in the end of all current models.

## Project Directory Structure

- `dataset/Chair` is the dataset folder that you need to place there yourself. Make sure that it's called exactly "Chair" and has `ops/ syms/` etc. folders within
- You can place your virtual environment into "virtual*" folder, where star means anything goes. All folders starting with "virtual" are ignored across the project.

## Guides

- To re-generate the `dataset/compiled` folder, ensure that there is `dataset/Chair` folder with all the dataset data within and run `dataset/json-compile.py` from within `dataset` folder.

# Non-technical details

## Roles

- **Iavor**: ML classificator
- **Maheep**: dataset parsing and data construction
- **Greg**: mesh correspondence and deformation
- **Vlad**: mesh correspondence and deformation

## Team information

- General Project Meeting - every Wednesday, 7:00 pm - 8:30 pm

## Timeline (2021)

- **March 31st** - Project Inception
- **April 7th** - Have dataset viewer ready to go
- **April 14th** - Crude and basic parts replacement, baseline sorting/scoring of the chairs
- **April 21th** - Refined parts replacement, scorer to sort the models
- **April 26th, 12:30 pm** - Project defense and submission (submission deadline is at 11:45 pm).

## General Project Idea

- Pick random mesh and turn it into its corresponding parts.
- Replace each corresponding part for some other part from the collection.
- Process the new part (deform, grow, scale, etc.) to make sure the chair is connected and coherent.
- Create several chairs like these and rank them by using our scoring mechanism.

## Deliverables

### Dataset viewer (April 7th) - Done

- First milestone, this will require several other parts in the works
- Basic UX: "explore" the dataset, able to choose any provided mesh, able to look at the mesh and then look at each of the particular parts constituting the mesh
- Basic UI: one set of arrows to move between the meshes and another set of arrows to move between the parts in a particular mesh (or anything else simple and effective)
- Requires mesh-parts association which in turn requires dataset processing

### MVP (April 14th) - Done

- First working version of the project.

### Refined MVP (April 21st) - In Progress

- Decent general functionality. Proper scoring and mesh welding.
