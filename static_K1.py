import os
import numpy
import sys
import platform
from operator import *
from abaqus import *
from abaqusConstants import *
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
from odbAccess import *

# input params
inp_data = dict()
with open('input.dat', 'r') as text:
    for line in text:
    	try:
            key, value = line.split('=')
            inp_data[key.strip()] = value.strip()
        except ValueError:
            pass

L   = float(inp_data['length'])
H   = float(inp_data['length'])
t   = float(inp_data['thickness'])
rho = float(inp_data['density'])
E   = float(inp_data['young'])
nu  = float(inp_data['poisson'])
F   = float(inp_data['force'])
cl  = float(inp_data['crack_length'])

model_name = 'toy_model'

min_r = 1.e-3
r = cl*0.1
if r < min_r:
    r = min_r

Ncontour = 5
Nhoop = 4
MeshCircle = r/5.0
MinEdgeMesh = H*0.01
MaxEdgeMesh = H*0.1
epsilon = 1e-5

# Ref: http://bertoldi.seas.harvard.edu/files/bertoldi/files/learnabaqusscriptinonehour.pdf
model = mdb.Model(name=model_name)
part = model.Part(name='Part 1', dimensionality=TWO_D_PLANAR, 
                  type=DEFORMABLE_BODY)

box_sketch = model.ConstrainedSketch(name='cantilever', sheetSize=1)
box_sketch.Line(point1=(0,0),point2=(L,0))
box_sketch.Line(point1=(L,0),point2=(L,H))
box_sketch.Line(point1=(L,H),point2=(0,H))
box_sketch.Line(point1=(0,H),point2=(0,0))
part.BaseShell(sketch=box_sketch)

# Partitions
partition_sketch = model.ConstrainedSketch(name='Partition Sketch', sheetSize=1)
partition_sketch.Line(point1=(L,H/2), point2=(L-cl,H/2))
partition_sketch.CircleByCenterPerimeter(center=(L-cl,H/2), point1=(L-cl+r,H/2))
part.PartitionFaceBySketch(faces=part.faces, sketch=partition_sketch)
## Materials
material = model.Material(name='steel')
material.Density(table=((rho, ), ))
material.Elastic(table=((E, nu), ))
model.HomogeneousSolidSection(material='steel', name='steel_section', thickness=t)


## Section Assignments
part.Set(faces=part.faces.getByBoundingBox(xMin=0-epsilon, xMax=L+epsilon,
                                           yMin=0-epsilon, yMax=H+epsilon), 
         name=('Part_faces'))
part.SectionAssignment(region=Region(faces=part.sets['Part_faces'].faces), 
                       sectionName='steel_section', offset=0.0, 
                       offsetType=MIDDLE_SURFACE, 
                       thicknessAssignment=FROM_SECTION)


## Instance
assembly = model.rootAssembly
instance = assembly.Instance(name='Instance 1', part=part, dependent=OFF)

# crack tip
edges = instance.edges[0:0]
for point in [(L-cl+epsilon, H/2,0), (L-epsilon, H/2, 0)]:
    pickedEdge = instance.edges.findAt((point, ))
    edges += pickedEdge
assembly.Set(edges=edges, name='CrackSeamLine')
crack_vertices = instance.vertices.findAt(((L-cl,H/2,0),))
assembly.engineeringFeatures.ContourIntegral(
    collapsedElementAtTip=SINGLE_NODE,
    extensionDirectionMethod=Q_VECTORS,
    symmetric=OFF,
    midNodePosition=0.25,
    crackFront=Region(vertices=crack_vertices),
    crackTip=Region(vertices=crack_vertices),
    name=('Crack-tip'),
    qVectors=(((L,H/2,0.0), (L-cl,H/2,0.0)),)
    )

seam_edges = instance.edges[0:0]
seam_edges = seam_edges + assembly.sets['CrackSeamLine'].edges
assembly.engineeringFeatures.assignSeam(regions=Region(edges=seam_edges))

# fixed BC
edges = instance.edges[0:0]
edges +=  instance.edges.findAt(((0,0+epsilon,0), ))
region = assembly.Set(edges=edges, name='fixedBC_set')
fixedBC = model.DisplacementBC(name='fixed_BC',createStepName='Initial',region=region, u1=0.0, u2=0.0, u3=UNSET)

# Loading
model.StaticStep(name='Step-1', previous='Initial')
load_vertices = instance.vertices.findAt(((L,0,0),))
region = assembly.Set(vertices=load_vertices, name='LoadVertices')
model.ConcentratedForce(name='Load-1', createStepName='Step-1', 
                        region=region, cf2=-F, distributionType=UNIFORM, 
                        field='', localCsys=None)
# Output
model.fieldOutputRequests['F-Output-1'].setValues(variables=('S','U','RF', 
                                                                 'ENER','ELEN'))
model.HistoryOutputRequest(contourType=J_INTEGRAL, contourIntegral='Crack-tip', 
                           createStepName='Step-1', name='J-Integral', 
                           numberOfContours=Ncontour, rebar=EXCLUDE, 
                           sectionPoints=DEFAULT, 
                           stressInitializationStep='Initial');
model.HistoryOutputRequest(contourType=K_FACTORS, contourIntegral='Crack-tip', 
                           createStepName='Step-1', name='K-value', 
                           numberOfContours=Ncontour, rebar=EXCLUDE, 
                           sectionPoints=DEFAULT, 
                           stressInitializationStep='Initial');
model.HistoryOutputRequest(contourType=T_STRESS, contourIntegral='Crack-tip', 
                           createStepName='Step-1', name='T-Stress', 
                           numberOfContours=Ncontour, rebar=EXCLUDE, 
                           sectionPoints=DEFAULT, 
                           stressInitializationStep='Initial');

# Region Mesh Controls
assembly.seedPartInstance(regions=(instance, ), deviationFactor=0.1, 
                          minSizeFactor=0.1, size=MaxEdgeMesh)
pickedRegions = instance.faces.findAt(((0+epsilon, 0+epsilon,0),))
assembly.setMeshControls(regions=pickedRegions, technique=FREE,elemShape=TRI, 
                         allowMapped=False)
crack_faces = instance.faces.getByBoundingBox(xMin=L-cl-r,xMax=L-cl+r,
                                              yMin=H/2-r, yMax=H/2+r)
assembly.setMeshControls(regions=crack_faces, elemShape=QUAD_DOMINATED, 
                         technique=SWEEP)
# Assign Element Type
assembly.setElementType(elemTypes=(ElemType(elemCode=CPE8,elemLibrary=STANDARD),
                                   ElemType(elemCode=CPE6M, 
                                            elemLibrary=STANDARD)), 
                        regions=(instance.faces, ));

# Mesh seeding
pickedEdge = instance.edges.findAt(((0,0+epsilon,0), ))
#pickedEdge = instance.edges.getByBoundingBox(xMin=0,xMax=L, yMin=0, yMax=H)
assembly.seedEdgeByBias(biasMethod=DOUBLE, endEdges=pickedEdge, minSize=MinEdgeMesh, maxSize=MaxEdgeMesh, constraint=FINER)
pickedEdge = instance.edges.findAt(((0+epsilon, 0, 0), ))
if len(pickedEdge) > 0:
    vertices = pickedEdge[0].getVertices()
    x1 = instance.vertices[vertices[0]].pointOn[0][0]
    x2 = instance.vertices[vertices[1]].pointOn[0][0]
    if(x1 > x2):
        assembly.seedEdgeByBias(biasMethod=SINGLE, end1Edges=pickedEdge, 
                                minSize=MinEdgeMesh, maxSize=MaxEdgeMesh, 
                                constraint=FINER)
    else:
        assembly.seedEdgeByBias(biasMethod=SINGLE, end2Edges=pickedEdge, 
                                minSize=MinEdgeMesh, maxSize=MaxEdgeMesh, 
                                constraint=FINER)

assembly.seedEdgeBySize(edges=seam_edges, constraint=FINER, 
                        size=MinEdgeMesh, deviationFactor=0.1)


# Mesh Cracks
CrackTipCircle = instance.edges.getByBoundingBox(xMin=L-cl-r,xMax=L-cl+r,
                                                 yMin=H/2-r, yMax=H/2+r)
assembly.seedEdgeBySize(edges=CrackTipCircle, constraint=FINER, 
                        size=MeshCircle, deviationFactor=0.1)
# can be visualized in CAE
assembly.Set(edges=CrackTipCircle, name='CrackTipCircle') 
CrackTipInner = instance.edges.findAt(((L-cl+epsilon,H/2,0),))
assembly.seedEdgeByNumber(edges=CrackTipInner, constraint=FINER, 
                          number=Ncontour)
assembly.Set(edges=CrackTipInner, name='CrackTipInner')
assembly.generateMesh(regions=instance.faces,seedConstraintOverride=ON,
                      meshTechniqueOverride=OFF)


# Snpashot
session.viewports['Viewport: 1'].setValues(displayedObject=assembly)
session.viewports['Viewport: 1'].assemblyDisplay.setValues(mesh=ON,
                                                     optimizationTasks=OFF, 
                                                     geometricRestrictions=OFF, 
                                                     stopConditions=OFF)
session.viewports['Viewport: 1'].assemblyDisplay.meshOptions.setValues(meshTechnique=ON)
session.viewports['Viewport: 1'].view.setValues(nearPlane=30.,
                                                farPlane=31,
                                                width=L*2,
                                                height=L*2,
                                                viewOffsetX=0,
                                                viewOffsetY=0)
session.printToFile(fileName='mesh_01.png', format=PNG, canvasObjects=(
    session.viewports['Viewport: 1'], ))

# Save and submit
mdb.saveAs('Job-'+model_name)
job = mdb.Job(model=model_name, name='Job-'+model_name, numCpus=1)
job.submit(consistencyChecking=OFF)
job.waitForCompletion()
#
# Extracting results
session.openOdb(name='Job-'+model_name+'.odb',  readOnly=True)
output = session.odbs['Job-'+model_name+'.odb'];
#
# To find keys, 1) abaqus cae nogui 2) >>> print(output.steps.keys()) 
# 3) >>> print(output.steps['Step-1'].historyRegion.keys()) ...
tmp = output.steps['Step-1'].historyRegions['ElementSet  ALL ELEMENTS'].historyOutputs
K1_value = []
K2_value = []
J_value = []
T_value = []
Cpd_value = []
for item in tmp.keys():
    if item[0:2] == 'K1':
        K1_value.append(tmp[item].data[0][1])   
    if item[0:2] == 'K2':
        K2_value.append(tmp[item].data[0][1])    
    if item[0:2] == 'J ':
        J_value.append(tmp[item].data[0][1])   
    if item[0:2] == 'Cp':
        Cpd_value.append(tmp[item].data[0][1])
    if item[0:2] == 'T-':
        T_value.append(tmp[item].data[0][1])

f = open('summary_fracture.dat','w')
f.write('# K1 value\n')
for item in K1_value:
    f.write('%.4e '%(item))
f.write('\n')
f.write('# K2 value\n')
for item in K2_value:
    f.write('%.4e '%(item))
f.write('\n')
f.write('# J value\n')
for item in J_value:
    f.write('%.4e '%(item))
f.write('\n')
f.write('# T value\n')
for item in T_value:
    f.write('%.4e '%(item))
f.write('\n')
f.write('# Cpd value\n')
for item in Cpd_value:
    f.write('%.4e '%(item))
f.write('\n')
