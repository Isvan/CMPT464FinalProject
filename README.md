# CMPT 464 Final Project

## Roles

- Iavor: ML classificator
- Maheep: dataset parsing and data construction
- Greg: mesh correspondence and deformation
- Vlad: mesh correspondence and deformation

## Team information

- General Project Meeting - every Wednesday, 7:00 pm - 8:30 pm

## Timeline 

- **March 31, 2021** - Project Inception
- **April 7th** - Have dataset viewer ready to go
- **April 14th** - Crude and basic parts replacement, no scorer
- **April 21th** - Refined parts replacement, scorer to sort the models
- **April 23rd (assuming the worst)** - Project defense and submission.

## General Project Idea

- Pick random mesh and turn it into its corresponding parts.
- Replace each corresponding part for some other part from the collection.
- Process the new part (deform, grow, scale, etc.) to make sure the chair is connected and coherent.
- Create several chairs like these and rank them by using our scoring mechanism.

## Assignments/Tasks

### Scorer (Iavor)

- Input: .obj
- Output: normalized score, 0-1
- In the end we will just integrate the trained model
- Convert meshes to voxel / SDF representation for analysis

### Dataset parsing and preparation (Maheep)

- Input: our dataset
- Output: one big `.json` containing information about each mesh from the dataset
- Each mesh entry would have information from `/syms`, `/boxes`, etc. clapmed together in one spot
- For our project, we will need that `.json` and list of all `.obj`'s to do everything else

### Mesh correspondence and deformation (Vlad & Greg)

- Input: mesh1 and mesh2
- Output: mesh1 that occupies the same amount of space as mesh2
- Need to investigate whether we can just grow the bounding box, whether we need to find transformation or etc.
- General idea: find transformation from mesh1 and mesh2, apply that transformation to mesh1 and return
- MVP: find rigid transform
- Refined version: find non-rigid deformation

### Mesh data structure and mesh part generation (Not assigned)

- Input: the big `.json` and the `.obj`'s (basically our transformed dataset)
- Output: Generate parts `.objs` based on the dataset entry.
- Make sense of `.json` and construct representations which can be usable later on (e.g. here is a mesh and here is its parts, each part is labeled)

## Ideas/Suggestions

- Probably need to set up a separate meeting with the TA