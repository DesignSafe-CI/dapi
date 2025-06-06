### OpenSees TCL file for 1D Soil Column Analysis ### 
### AnalysisID: TestProfileB ### 
### Ground Motion Record: RSN6928 ###
### Slope Inclination: 2.00 % ###


### GENERATING MESH ###
wipe
model BasicBuilder -ndm 2 -ndf 3
node 1 0.00 0.00
node 2 0.50 0.00
node 3 0.00 0.50
node 4 0.50 0.50
node 5 0.00 1.00
node 6 0.50 1.00
node 7 0.00 1.50
node 8 0.50 1.50
node 9 0.00 2.00
node 10 0.50 2.00
node 11 0.00 2.50
node 12 0.50 2.50
node 13 0.00 3.00
node 14 0.50 3.00
node 15 0.00 3.50
node 16 0.50 3.50
node 17 0.00 4.00
node 18 0.50 4.00
node 19 0.00 4.50
node 20 0.50 4.50
node 21 0.00 5.00
node 22 0.50 5.00
node 23 0.00 5.50
node 24 0.50 5.50
node 25 0.00 6.00
node 26 0.50 6.00
node 27 0.00 6.50
node 28 0.50 6.50
node 29 0.00 7.00
node 30 0.50 7.00
node 31 0.00 7.50
node 32 0.50 7.50
node 33 0.00 8.00
node 34 0.50 8.00
node 35 0.00 8.50
node 36 0.50 8.50
node 37 0.00 9.00
node 38 0.50 9.00
node 39 0.00 9.50
node 40 0.50 9.50
node 41 0.00 10.00
node 42 0.50 10.00
node 43 0.00 10.50
node 44 0.50 10.50
node 45 0.00 11.00
node 46 0.50 11.00
node 47 0.00 11.50
node 48 0.50 11.50
node 49 0.00 12.00
node 50 0.50 12.00
node 51 0.00 12.50
node 52 0.50 12.50
node 53 0.00 13.00
node 54 0.50 13.00
node 55 0.00 13.50
node 56 0.50 13.50
node 57 0.00 14.00
node 58 0.50 14.00
node 59 0.00 14.50
node 60 0.50 14.50
node 61 0.00 15.00
node 62 0.50 15.00
node 63 0.00 15.50
node 64 0.50 15.50
node 65 0.00 16.00
node 66 0.50 16.00
node 67 0.00 16.50
node 68 0.50 16.50
node 69 0.00 17.00
node 70 0.50 17.00
node 71 0.00 17.50
node 72 0.50 17.50
node 73 0.00 18.00
node 74 0.50 18.00


 ### NODE BOUNDARY CONDITIONS ###
fix 1 0 1 0
fix 2 0 1 0
equalDOF 1 2 1
equalDOF 3 4 1 2
equalDOF 5 6 1 2
equalDOF 7 8 1 2
equalDOF 9 10 1 2
equalDOF 11 12 1 2
equalDOF 13 14 1 2
equalDOF 15 16 1 2
equalDOF 17 18 1 2
equalDOF 19 20 1 2
equalDOF 21 22 1 2
equalDOF 23 24 1 2
equalDOF 25 26 1 2
equalDOF 27 28 1 2
equalDOF 29 30 1 2
equalDOF 31 32 1 2
equalDOF 33 34 1 2
equalDOF 35 36 1 2
equalDOF 37 38 1 2
equalDOF 39 40 1 2
equalDOF 41 42 1 2
equalDOF 43 44 1 2
equalDOF 45 46 1 2
equalDOF 47 48 1 2
equalDOF 49 50 1 2
equalDOF 51 52 1 2
equalDOF 53 54 1 2
equalDOF 55 56 1 2
equalDOF 57 58 1 2
equalDOF 59 60 1 2
equalDOF 61 62 1 2
equalDOF 63 64 1 2
equalDOF 65 66 1 2
equalDOF 67 68 1 2
equalDOF 69 70 1 2
equalDOF 71 72 1 2
equalDOF 73 74 1 2
fix 65 0 0 1
fix 66 0 0 1
fix 67 0 0 1
fix 68 0 0 1
fix 69 0 0 1
fix 70 0 0 1
fix 71 0 0 1
fix 72 0 0 1
fix 73 0 0 1
fix 74 0 0 1



 ### GENERATE SOIL MATERIAL MODELS ###
nDMaterial PM4Sand 1 0.950 11638.8 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 2 0.950 10464.4 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 3 0.950 9412.1 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 4 0.950 8469.0 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 5 0.950 7623.8 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 6 0.950 6866.0 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 7 0.950 6186.5 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 8 0.950 5577.2 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 9 0.950 5030.7 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 10 0.950 4540.4 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 11 0.950 4100.5 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 12 0.950 3705.8 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 13 0.950 3351.5 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 14 0.950 3033.5 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 15 0.950 2748.0 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 16 0.950 2491.7 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 17 0.950 2261.7 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 18 0.950 2055.2 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 19 0.950 1869.9 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 20 0.950 1703.6 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 21 0.950 1554.5 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 22 0.950 1420.9 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 23 0.950 1301.3 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 24 0.950 1194.4 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 25 0.950 1099.0 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 26 0.950 1014.2 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 27 0.950 939.2 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 28 0.950 873.3 2.500 2.102 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 29 0.700 835.7 0.440 2.050 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333
nDMaterial PM4Sand 30 0.400 524.4 1.500 1.589 101.300 -1 0.800 0.500 0.500 0.100 -1 -1 250.0 -1 33.000 0.333



 ### DEFINE SOIL ELEMENTS ###
element SSPquadUP 1 1 2 4 3 1 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 2 3 4 6 5 2 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 3 5 6 8 7 3 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 4 7 8 10 9 4 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 5 9 10 12 11 5 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 6 11 12 14 13 6 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 7 13 14 16 15 7 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 8 15 16 18 17 8 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 9 17 18 20 19 9 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 10 19 20 22 21 10 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 11 21 22 24 23 11 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 12 23 24 26 25 12 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 13 25 26 28 27 13 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 14 27 28 30 29 14 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 15 29 30 32 31 15 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 16 31 32 34 33 16 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 17 33 34 36 35 17 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 18 35 36 38 37 18 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 19 37 38 40 39 19 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 20 39 40 42 41 20 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 21 41 42 44 43 21 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 22 43 44 46 45 22 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 23 45 46 48 47 23 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 24 47 48 50 49 24 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 25 49 50 52 51 25 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 26 51 52 54 53 26 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 27 53 54 56 55 27 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 28 55 56 58 57 28 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.515 1.000e-08 -0.196 -9.808
element SSPquadUP 29 57 58 60 59 29 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.590 1.000e-08 -0.196 -9.808
element SSPquadUP 30 59 60 62 61 29 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.590 1.000e-08 -0.196 -9.808
element SSPquadUP 31 61 62 64 63 29 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.590 1.000e-08 -0.196 -9.808
element SSPquadUP 32 63 64 66 65 29 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.590 1.000e-08 -0.196 -9.808
element SSPquadUP 33 65 66 68 67 30 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.680 1.000e-08 -0.196 -9.808
element SSPquadUP 34 67 68 70 69 30 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.680 1.000e-08 -0.196 -9.808
element SSPquadUP 35 69 70 72 71 30 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.680 1.000e-08 -0.196 -9.808
element SSPquadUP 36 71 72 74 73 30 1.000 2.200e+06 1.000 1.000e+00 1.000e+00 0.680 1.000e-08 -0.196 -9.808



### LYSMER-KUHLMEYER DASHPOTS ###
model BasicBuilder -ndm 2 -ndf 2
node 75 0.00 0.00
node 76 0.00 0.00
fix 75 1 1
fix 76 0 1
equalDOF 1 76 1
uniaxialMaterial Viscous 4000 843.528 1
element zeroLength 5000 75 76 -mat 4000 -dir 1



 ### GRAVITY RECORDERS  ###
eval "recorder Element -file ProfileB_Gstress$motionID.out -time -eleRange 1 36 stress"


## Update Material for Elastoplastic ##
updateMaterialStage -material 1 -stage 0
updateMaterialStage -material 2 -stage 0
updateMaterialStage -material 3 -stage 0
updateMaterialStage -material 4 -stage 0
updateMaterialStage -material 5 -stage 0
updateMaterialStage -material 6 -stage 0
updateMaterialStage -material 7 -stage 0
updateMaterialStage -material 8 -stage 0
updateMaterialStage -material 9 -stage 0
updateMaterialStage -material 10 -stage 0
updateMaterialStage -material 11 -stage 0
updateMaterialStage -material 12 -stage 0
updateMaterialStage -material 13 -stage 0
updateMaterialStage -material 14 -stage 0
updateMaterialStage -material 15 -stage 0
updateMaterialStage -material 16 -stage 0
updateMaterialStage -material 17 -stage 0
updateMaterialStage -material 18 -stage 0
updateMaterialStage -material 19 -stage 0
updateMaterialStage -material 20 -stage 0
updateMaterialStage -material 21 -stage 0
updateMaterialStage -material 22 -stage 0
updateMaterialStage -material 23 -stage 0
updateMaterialStage -material 24 -stage 0
updateMaterialStage -material 25 -stage 0
updateMaterialStage -material 26 -stage 0
updateMaterialStage -material 27 -stage 0
updateMaterialStage -material 28 -stage 0
updateMaterialStage -material 29 -stage 0
updateMaterialStage -material 30 -stage 0



### APPLY GRAVITY LOADING ELASTIC CASE ###
constraints Transformation
test NormDispIncr 1.00e-04 35 2
algorithm Newton
numberer RCM
system SparseGeneral
integrator Newmark 0.833 0.444
analysis Transient
analyze 10 1.00



 ### ELASTO-PLASTIC GRAVITY ANALYSIS ###
updateMaterialStage -material 1 -stage 1
setParameter -value 0.300 -eleRange 1 1 poissonRatio 1
setParameter -value 0 -eleRange 1 1 FirstCall 1
updateMaterialStage -material 2 -stage 1
setParameter -value 0.300 -eleRange 2 2 poissonRatio 2
setParameter -value 0 -eleRange 2 2 FirstCall 2
updateMaterialStage -material 3 -stage 1
setParameter -value 0.300 -eleRange 3 3 poissonRatio 3
setParameter -value 0 -eleRange 3 3 FirstCall 3
updateMaterialStage -material 4 -stage 1
setParameter -value 0.300 -eleRange 4 4 poissonRatio 4
setParameter -value 0 -eleRange 4 4 FirstCall 4
updateMaterialStage -material 5 -stage 1
setParameter -value 0.300 -eleRange 5 5 poissonRatio 5
setParameter -value 0 -eleRange 5 5 FirstCall 5
updateMaterialStage -material 6 -stage 1
setParameter -value 0.300 -eleRange 6 6 poissonRatio 6
setParameter -value 0 -eleRange 6 6 FirstCall 6
updateMaterialStage -material 7 -stage 1
setParameter -value 0.300 -eleRange 7 7 poissonRatio 7
setParameter -value 0 -eleRange 7 7 FirstCall 7
updateMaterialStage -material 8 -stage 1
setParameter -value 0.300 -eleRange 8 8 poissonRatio 8
setParameter -value 0 -eleRange 8 8 FirstCall 8
updateMaterialStage -material 9 -stage 1
setParameter -value 0.300 -eleRange 9 9 poissonRatio 9
setParameter -value 0 -eleRange 9 9 FirstCall 9
updateMaterialStage -material 10 -stage 1
setParameter -value 0.300 -eleRange 10 10 poissonRatio 10
setParameter -value 0 -eleRange 10 10 FirstCall 10
updateMaterialStage -material 11 -stage 1
setParameter -value 0.300 -eleRange 11 11 poissonRatio 11
setParameter -value 0 -eleRange 11 11 FirstCall 11
updateMaterialStage -material 12 -stage 1
setParameter -value 0.300 -eleRange 12 12 poissonRatio 12
setParameter -value 0 -eleRange 12 12 FirstCall 12
updateMaterialStage -material 13 -stage 1
setParameter -value 0.300 -eleRange 13 13 poissonRatio 13
setParameter -value 0 -eleRange 13 13 FirstCall 13
updateMaterialStage -material 14 -stage 1
setParameter -value 0.300 -eleRange 14 14 poissonRatio 14
setParameter -value 0 -eleRange 14 14 FirstCall 14
updateMaterialStage -material 15 -stage 1
setParameter -value 0.300 -eleRange 15 15 poissonRatio 15
setParameter -value 0 -eleRange 15 15 FirstCall 15
updateMaterialStage -material 16 -stage 1
setParameter -value 0.300 -eleRange 16 16 poissonRatio 16
setParameter -value 0 -eleRange 16 16 FirstCall 16
updateMaterialStage -material 17 -stage 1
setParameter -value 0.300 -eleRange 17 17 poissonRatio 17
setParameter -value 0 -eleRange 17 17 FirstCall 17
updateMaterialStage -material 18 -stage 1
setParameter -value 0.300 -eleRange 18 18 poissonRatio 18
setParameter -value 0 -eleRange 18 18 FirstCall 18
updateMaterialStage -material 19 -stage 1
setParameter -value 0.300 -eleRange 19 19 poissonRatio 19
setParameter -value 0 -eleRange 19 19 FirstCall 19
updateMaterialStage -material 20 -stage 1
setParameter -value 0.300 -eleRange 20 20 poissonRatio 20
setParameter -value 0 -eleRange 20 20 FirstCall 20
updateMaterialStage -material 21 -stage 1
setParameter -value 0.300 -eleRange 21 21 poissonRatio 21
setParameter -value 0 -eleRange 21 21 FirstCall 21
updateMaterialStage -material 22 -stage 1
setParameter -value 0.300 -eleRange 22 22 poissonRatio 22
setParameter -value 0 -eleRange 22 22 FirstCall 22
updateMaterialStage -material 23 -stage 1
setParameter -value 0.300 -eleRange 23 23 poissonRatio 23
setParameter -value 0 -eleRange 23 23 FirstCall 23
updateMaterialStage -material 24 -stage 1
setParameter -value 0.300 -eleRange 24 24 poissonRatio 24
setParameter -value 0 -eleRange 24 24 FirstCall 24
updateMaterialStage -material 25 -stage 1
setParameter -value 0.300 -eleRange 25 25 poissonRatio 25
setParameter -value 0 -eleRange 25 25 FirstCall 25
updateMaterialStage -material 26 -stage 1
setParameter -value 0.300 -eleRange 26 26 poissonRatio 26
setParameter -value 0 -eleRange 26 26 FirstCall 26
updateMaterialStage -material 27 -stage 1
setParameter -value 0.300 -eleRange 27 27 poissonRatio 27
setParameter -value 0 -eleRange 27 27 FirstCall 27
updateMaterialStage -material 28 -stage 1
setParameter -value 0.300 -eleRange 28 28 poissonRatio 28
setParameter -value 0 -eleRange 28 28 FirstCall 28
updateMaterialStage -material 29 -stage 1
setParameter -value 0.300 -eleRange 29 32 poissonRatio 29
setParameter -value 0 -eleRange 29 32 FirstCall 29
updateMaterialStage -material 30 -stage 1
setParameter -value 0.300 -eleRange 33 36 poissonRatio 30
setParameter -value 0 -eleRange 33 36 FirstCall 30
analyze 10 1.000
remove sp 1 1
remove recorders



 ### DYNAMIC ANALYSIS PHASE ###

# Updating Element Permeabilities#
setParameter -val 3.058e-06 -eleRange 1 1 hPerm
setParameter -val 3.058e-06 -eleRange 1 1 vPerm
setParameter -val 3.058e-06 -eleRange 2 2 hPerm
setParameter -val 3.058e-06 -eleRange 2 2 vPerm
setParameter -val 3.058e-06 -eleRange 3 3 hPerm
setParameter -val 3.058e-06 -eleRange 3 3 vPerm
setParameter -val 3.058e-06 -eleRange 4 4 hPerm
setParameter -val 3.058e-06 -eleRange 4 4 vPerm
setParameter -val 3.058e-06 -eleRange 5 5 hPerm
setParameter -val 3.058e-06 -eleRange 5 5 vPerm
setParameter -val 3.058e-06 -eleRange 6 6 hPerm
setParameter -val 3.058e-06 -eleRange 6 6 vPerm
setParameter -val 3.058e-06 -eleRange 7 7 hPerm
setParameter -val 3.058e-06 -eleRange 7 7 vPerm
setParameter -val 3.058e-06 -eleRange 8 8 hPerm
setParameter -val 3.058e-06 -eleRange 8 8 vPerm
setParameter -val 3.058e-06 -eleRange 9 9 hPerm
setParameter -val 3.058e-06 -eleRange 9 9 vPerm
setParameter -val 3.058e-06 -eleRange 10 10 hPerm
setParameter -val 3.058e-06 -eleRange 10 10 vPerm
setParameter -val 3.058e-06 -eleRange 11 11 hPerm
setParameter -val 3.058e-06 -eleRange 11 11 vPerm
setParameter -val 3.058e-06 -eleRange 12 12 hPerm
setParameter -val 3.058e-06 -eleRange 12 12 vPerm
setParameter -val 3.058e-06 -eleRange 13 13 hPerm
setParameter -val 3.058e-06 -eleRange 13 13 vPerm
setParameter -val 3.058e-06 -eleRange 14 14 hPerm
setParameter -val 3.058e-06 -eleRange 14 14 vPerm
setParameter -val 3.058e-06 -eleRange 15 15 hPerm
setParameter -val 3.058e-06 -eleRange 15 15 vPerm
setParameter -val 3.058e-06 -eleRange 16 16 hPerm
setParameter -val 3.058e-06 -eleRange 16 16 vPerm
setParameter -val 3.058e-06 -eleRange 17 17 hPerm
setParameter -val 3.058e-06 -eleRange 17 17 vPerm
setParameter -val 3.058e-06 -eleRange 18 18 hPerm
setParameter -val 3.058e-06 -eleRange 18 18 vPerm
setParameter -val 3.058e-06 -eleRange 19 19 hPerm
setParameter -val 3.058e-06 -eleRange 19 19 vPerm
setParameter -val 3.058e-06 -eleRange 20 20 hPerm
setParameter -val 3.058e-06 -eleRange 20 20 vPerm
setParameter -val 3.058e-06 -eleRange 21 21 hPerm
setParameter -val 3.058e-06 -eleRange 21 21 vPerm
setParameter -val 3.058e-06 -eleRange 22 22 hPerm
setParameter -val 3.058e-06 -eleRange 22 22 vPerm
setParameter -val 3.058e-06 -eleRange 23 23 hPerm
setParameter -val 3.058e-06 -eleRange 23 23 vPerm
setParameter -val 3.058e-06 -eleRange 24 24 hPerm
setParameter -val 3.058e-06 -eleRange 24 24 vPerm
setParameter -val 3.058e-06 -eleRange 25 25 hPerm
setParameter -val 3.058e-06 -eleRange 25 25 vPerm
setParameter -val 3.058e-06 -eleRange 26 26 hPerm
setParameter -val 3.058e-06 -eleRange 26 26 vPerm
setParameter -val 3.058e-06 -eleRange 27 27 hPerm
setParameter -val 3.058e-06 -eleRange 27 27 vPerm
setParameter -val 3.058e-06 -eleRange 28 28 hPerm
setParameter -val 3.058e-06 -eleRange 28 28 vPerm
setParameter -val 3.058e-06 -eleRange 29 32 hPerm
setParameter -val 3.058e-06 -eleRange 29 32 vPerm
setParameter -val 1.019e-09 -eleRange 33 36 hPerm
setParameter -val 1.019e-09 -eleRange 33 36 vPerm

 # Creating Post-Gravity Recorders
setTime 0.000
wipeAnalysis
eval "recorder Node -file ProfileB_acc$motionID.out -time -dT 0.010 -node 55 74 -dof 1 accel"


# Creating Force Load Pattern
set mSeries "Path -dt $motionDT -filePath $velocityFile -factor 885.202"

pattern Plain 10 $mSeries {load 1 1.000 0.000 0.000}

# Analysis Time Step
set dT $motionDT
set nSteps $motionSteps

 ## Setting Dynamic Analysis Parameters##
constraints Transformation
test NormDispIncr 1.000e-04 15 0
algorithm Newton
numberer RCM
system SparseGeneral
integrator Newmark 0.500 0.250
analysis Transient
rayleigh 4.977e-02 3.152e-04 0.000 0.000



 ## Define Dynamic Sub-stepping ##
proc subStepAnalyze {dT subStep} {
	if {$subStep > 10} {
		return -10
	}
	for {set i 1} {$i < 3} {incr i} {
		puts "Try dT = $dT"
		set success [analyze 1 $dT]
		if {$success != 0} {
			set success [subStepAnalyze [expr $dT/2.0] [expr $subStep+1]]
			if {$success == -10} {
				puts "Did not converge."
				return $success
			}
		} else {
			if {$i==1} {
				puts "Substep $subStep : Left side converged with dT = $dT"
			} else {
				puts "Substep $subStep : Right side converged with dT = $dT"
			}
		}
	}
	return $success
}
 # Start Dynamic Analysis #
set remStep $nSteps
set success 0
puts "Start analysis"
set startT [clock seconds]
while {$success != -10} {
	set subStep 0
	set success [analyze $remStep $dT]
	if {$success == 0} {
		 puts "Analysis Finished"
		break
	} else {
		set curTime [getTime]
		puts "Analysis failed at $curTime. Try substepping."
		set success [subStepAnalyze [expr $dT/2.0] [incr subStep]]
		set curStep  [expr int($curTime/$dT + 1)]
		set remStep  [expr int($nSteps-$curStep)]
		puts "Current step: $curStep , Remaining steps: $remStep"
	}
}
set endT [clock seconds]

puts "loading analysis execution time: [expr $endT-$startT] seconds."
puts "Finished with dynamic analysis..."
wipe
