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
with open('cantilever.inp', 'r') as text:
    for line in text:
    	try:
            key, value = line.split('=')
            inp_data[key.strip()] = value.strip()
        except ValueError:
            pass

L   = float(inp_data['length'])
H   = float(inp_data['height'])
t   = float(inp_data['thickness'])
E   = float(inp_data['young'])
nu  = float(inp_data['poisson'])
F   = float(inp_data['force'])
mat = inp_data['material_name']

model_name = 'toy_model'
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


## Materials
material = model.Material(name=mat)
material.Elastic(table=((E, nu), ))
model.HomogeneousSolidSection(material=mat, name='glass_section', thickness=t)


## Section Assignments
part.Set(faces=part.faces.getByBoundingBox(xMin=0-epsilon, xMax=L+epsilon,
                                           yMin=0-epsilon, yMax=H+epsilon), 
         name=('Part_faces'))
part.SectionAssignment(region=Region(faces=part.sets['Part_faces'].faces), 
                       sectionName='glass_section', offset=0.0, 
                       offsetType=MIDDLE_SURFACE, 
                       thicknessAssignment=FROM_SECTION)


## Instance
assembly = model.rootAssembly
instance = assembly.Instance(name='Instance 1', part=part, dependent=OFF)

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

# Region Mesh Controls
assembly.seedPartInstance(regions=(instance, ), deviationFactor=0.1, 
                          minSizeFactor=0.1, size=5)
pickedRegions = instance.faces.findAt(((0+epsilon, 0+epsilon,0),))
assembly.setMeshControls(regions=pickedRegions, technique=STRUCTURED,
                         elemShape=QUAD)

# Assign Element Type
assembly.setElementType(elemTypes=(ElemType(elemCode=CPE8,elemLibrary=STANDARD),
                                   ElemType(elemCode=CPE6M, 
                                            elemLibrary=STANDARD)), 
                        regions=(instance.faces, ));

# Meshing
assembly.generateMesh(regions=instance.faces,seedConstraintOverride=ON,
                      meshTechniqueOverride=OFF)

## Snpashot
session.viewports['Viewport: 1'].setValues(displayedObject=assembly)
session.viewports['Viewport: 1'].assemblyDisplay.setValues(mesh=ON,
                                                     optimizationTasks=OFF, 
                                                     geometricRestrictions=OFF, 
                                                     stopConditions=OFF)
session.viewports['Viewport: 1'].assemblyDisplay.meshOptions.setValues(meshTechnique=ON)
session.viewports['Viewport: 1'].view.setValues(nearPlane=200.,
                                                farPlane=211,
                                                width=180,
                                                height=30,
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
session.viewports['Viewport: 1'].setValues(displayedObject=output)
session.viewports['Viewport: 1'].odbDisplay.display.setValues(plotState=(
    CONTOURS_ON_DEF, ))
session.viewports['Viewport: 1'].view.setValues(nearPlane=222.363, 
    farPlane=354.525, width=106.603, height=31.7695, viewOffsetX=-0.711316, 
    viewOffsetY=0.0693371)
session.printToFile(fileName='contour_01.png', format=PNG, canvasObjects=(
    session.viewports['Viewport: 1'], ))

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
with open('cantilever.inp', 'r') as text:
    for line in text:
    	try:
            key, value = line.split('=')
            inp_data[key.strip()] = value.strip()
        except ValueError:
            pass

L   = float(inp_data['length'])
H   = float(inp_data['height'])
t   = float(inp_data['thickness'])
E   = float(inp_data['young'])
nu  = float(inp_data['poisson'])
F   = float(inp_data['force'])
mat = inp_data['material_name']

model_name = 'toy_model'
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


## Materials
material = model.Material(name=mat)
material.Elastic(table=((E, nu), ))
model.HomogeneousSolidSection(material=mat, name='glass_section', thickness=t)


## Section Assignments
part.Set(faces=part.faces.getByBoundingBox(xMin=0-epsilon, xMax=L+epsilon,
                                           yMin=0-epsilon, yMax=H+epsilon), 
         name=('Part_faces'))
part.SectionAssignment(region=Region(faces=part.sets['Part_faces'].faces), 
                       sectionName='glass_section', offset=0.0, 
                       offsetType=MIDDLE_SURFACE, 
                       thicknessAssignment=FROM_SECTION)


## Instance
assembly = model.rootAssembly
instance = assembly.Instance(name='Instance 1', part=part, dependent=OFF)

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

# Region Mesh Controls
assembly.seedPartInstance(regions=(instance, ), deviationFactor=0.1, 
                          minSizeFactor=0.1, size=5)
pickedRegions = instance.faces.findAt(((0+epsilon, 0+epsilon,0),))
assembly.setMeshControls(regions=pickedRegions, technique=STRUCTURED,
                         elemShape=QUAD)

# Assign Element Type
assembly.setElementType(elemTypes=(ElemType(elemCode=CPE8,elemLibrary=STANDARD),
                                   ElemType(elemCode=CPE6M, 
                                            elemLibrary=STANDARD)), 
                        regions=(instance.faces, ));

# Meshing
assembly.generateMesh(regions=instance.faces,seedConstraintOverride=ON,
                      meshTechniqueOverride=OFF)

## Snpashot
session.viewports['Viewport: 1'].setValues(displayedObject=assembly)
session.viewports['Viewport: 1'].assemblyDisplay.setValues(mesh=ON,
                                                     optimizationTasks=OFF, 
                                                     geometricRestrictions=OFF, 
                                                     stopConditions=OFF)
session.viewports['Viewport: 1'].assemblyDisplay.meshOptions.setValues(meshTechnique=ON)
session.viewports['Viewport: 1'].view.setValues(nearPlane=200.,
                                                farPlane=211,
                                                width=180,
                                                height=30,
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
session.viewports['Viewport: 1'].setValues(displayedObject=output)
session.viewports['Viewport: 1'].odbDisplay.display.setValues(plotState=(
    CONTOURS_ON_DEF, ))
session.viewports['Viewport: 1'].view.setValues(nearPlane=222.363, 
    farPlane=354.525, width=106.603, height=31.7695, viewOffsetX=-0.711316, 
    viewOffsetY=0.0693371)
session.printToFile(fileName='contour_01.png', format=PNG, canvasObjects=(
    session.viewports['Viewport: 1'], ))

