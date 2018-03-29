

import sys
import vtk
from PyQt5 import QtGui, QtCore, QtWidgets
# from vtk.qt4.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtCore import pyqtSlot
import vtk

aRenderer = vtk.vtkRenderer()
# renWin = vtk.vtkRenderWindow()
# renWin.AddRenderer(aRenderer)
# iren = vtk.vtkRenderWindowInteractor()
# iren.SetRenderWindow(renWin)

# The following reader is used to read a series of 2D slices (images)
# that compose the volume. The slice dimensions are set, and the
# pixel spacing. The data Endianness must also be specified. The reader
# usese the FilePrefix in combination with the slice number to construct
# the mesh
v16 = vtk.vtkVolume16Reader()
v16.SetDataDimensions(64, 64)
v16.SetDataByteOrderToLittleEndian()
v16.SetFilePrefix("./VTKData/data/headsq/quarter")
v16.SetImageRange(1, 93)
v16.SetDataSpacing(3.2, 3.2, 1.5)

isoValues = [500, 2700, 1150]
colors = [(1, 0.67, 0.37), (0.5, 1, 0.37),
          (1.0, 1.0, 0.9), (1, 0.67, 0.37), (1.0, 1.0, 0.9)]

for idx, iso in enumerate(isoValues):

    extractor = vtk.vtkMarchingCubes()
    extractor.SetInputConnection(v16.GetOutputPort())
    extractor.SetValue(0, iso)

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(extractor.GetOutputPort())
    normals.SetFeatureAngle(60.0)

    stripper = vtk.vtkStripper()
    stripper.SetInputConnection(normals.GetOutputPort())

    locator = vtk.vtkCellLocator()
    locator.SetDataSet(extractor.GetOutput())
    locator.LazyEvaluationOn()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(stripper.GetOutputPort())
    mapper.ScalarVisibilityOff()

    property = vtk.vtkProperty()
    property.SetColor(colors[idx])

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.SetProperty(property)
    aRenderer.AddActor(actor)

aCamera = vtk.vtkCamera()
aCamera.SetViewUp(0, 0, -1)
aCamera.SetPosition(0, 1, 0)


txt = vtk.vtkTextActor()
txt.SetInput("Opacity: ")
txtprop = txt.GetTextProperty()
txtprop.SetFontFamilyToArial()
txtprop.SetFontSize(18)
txtprop.SetColor(0, 0, 0)
txt.SetDisplayPosition(20, 30)

aRenderer.AddActor(txt)
# aRenderer.GetActors()
aRenderer.SetActiveCamera(aCamera)
aRenderer.ResetCamera()
aRenderer.SetBackground(0.8, 0.8, 0.8)


class MainWindow(QtWidgets.QMainWindow):

    class EventsHandler(vtk.vtkInteractorStyleTrackballCamera):

        def __init__(self, txt, iren=None):
            self.iren = iren
            self.prevOpacity = 1
            self.clickPos = ()
            self.NewPickedActor = None
            self.LastPickedActor = None
            self.LastPickedProperty = vtk.vtkProperty()
            self.translationDelta = 1.5
            self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)
            self.AddObserver("KeyPressEvent", self.keyPressEvent)
            self.txt = txt

        def keyPressEvent(self, obj, event):
            if not self.NewPickedActor:
                return
            key = self.iren.GetKeySym()
            # print(key)
            opacity = self.NewPickedActor.GetProperty().GetOpacity()
            if key == "Up":
                opacity += 0.1
                opacity = min(opacity, 1)
                self.NewPickedActor.GetProperty().SetOpacity(opacity)
                txt.SetInput("Opacity :" + "{0:.4f}".format(opacity))
            if key == "Down":
                opacity -= 0.1
                opacity = max(opacity, 0.05)
                self.NewPickedActor.GetProperty().SetOpacity(opacity)
                txt.SetInput("Opacity :" + "{0:.4f}".format(opacity))
            oldPosition = self.NewPickedActor.GetPosition()
            if key == "g":
                self.NewPickedActor.SetPosition(
                    oldPosition[0] - self.translationDelta, oldPosition[1], oldPosition[2])
            if key == "j":
                self.NewPickedActor.SetPosition(
                    oldPosition[0] + self.translationDelta, oldPosition[1], oldPosition[2])
            if key == "y":
                self.NewPickedActor.SetPosition(
                    oldPosition[0], oldPosition[1], oldPosition[2] - self.translationDelta)
            if key == "h":
                self.NewPickedActor.SetPosition(
                    oldPosition[0], oldPosition[1], oldPosition[2] + self.translationDelta)
        #    self.LastPickedProperty.DeepCopy(self.NewPickedActor.GetProperty())
            self.prevOpacity = self.NewPickedActor.GetProperty().GetOpacity()
            self.OnKeyPress()
            self.iren.Render()

            return
            # print(obj)

        def leftButtonPressEvent(self, obj, event):
            clickPos = self.GetInteractor().GetEventPosition()
            #  used to pick an actor/prop given a selection point (in display coordinates) and a renderer.
            picker = vtk.vtkPropPicker()
            picker.Pick(clickPos[0], clickPos[1], 0, self.GetDefaultRenderer())

            self.NewPickedActor = picker.GetActor()

            # If something was selected
            if self.NewPickedActor:
                # If we picked something before, reset its property
                if self.LastPickedActor:
                    self.LastPickedActor.GetProperty().DeepCopy(self.LastPickedProperty)
                    self.LastPickedActor.GetProperty().SetOpacity(self.prevOpacity)

                # Save the property of the picked actor so that we can
                # restore it next time

                self.LastPickedProperty.DeepCopy(
                    self.NewPickedActor.GetProperty())
                # Highlight the picked actor
                self.NewPickedActor.GetProperty().SetColor(0.0, 0.8, 0.5)

                opacity = self.NewPickedActor.GetProperty().GetOpacity()
                txt.SetInput("Opacity :" + "{0:.4f}".format(opacity))
                self.LastPickedActor = self.NewPickedActor

            else:
                if self.LastPickedActor:
                    self.LastPickedActor.GetProperty().DeepCopy(self.LastPickedProperty)
                    self.LastPickedActor.GetProperty().SetOpacity(self.prevOpacity)
                    txt.SetInput("Opacity :")
            self.OnLeftButtonDown()
            return

    def __init__(self, ren):

        # QtWidgets.QMainWindow.__init__(self, parent)

        super().__init__()
        self.frame = QtWidgets.QFrame()

        self.vl = QtWidgets.QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.vl.addWidget(self.vtkWidget)

        self.ren = ren

        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        # self.iren = QVTKRenderWindowInteractor(self)
        # self.EventsHandler
        style = self.EventsHandler(txt, self.iren)
        style.SetDefaultRenderer(self.ren)
        self.iren.SetInteractorStyle(style)
        # self.ren.ResetCamera()
        self.st = style
        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)
        self.initUI()
        self.show()
        self.iren.Initialize()

    def initUI(self):

        button1 = QPushButton('Increase', self)
        # button.setToolTip('This is an example button')
        button1.move(10, 10)
        button1.clicked.connect(self.on_click1)
        button2 = QPushButton('Decrease', self)
        # button.setToolTip('This is an example button')
        button2.move(10, 40)
        button2.clicked.connect(self.on_click2)
        self.show()

    @pyqtSlot()
    def on_click1(self):
        if not self.st.LastPickedActor or not self.st.NewPickedActor:
            return
        opacity = self.st.LastPickedActor.GetProperty().GetOpacity()
        opacity += 0.1
        opacity = min(opacity, 1)
        self.st.LastPickedActor.GetProperty().SetOpacity(opacity)
        self.st.txt.SetInput("Opacity :" + "{0:.4f}".format(opacity))
        self.st.prevOpacity = self.st.NewPickedActor.GetProperty().GetOpacity()
        self.st.iren.Render()

    @pyqtSlot()
    def on_click2(self):
        if not self.st.LastPickedActor or not self.st.NewPickedActor:
            return
        opacity = self.st.LastPickedActor.GetProperty().GetOpacity()
        opacity -= 0.1
        opacity = max(opacity, 0.05)
        self.st.LastPickedActor.GetProperty().SetOpacity(opacity)
        self.st.txt.SetInput("Opacity :" + "{0:.4f}".format(opacity))
        self.st.prevOpacity = self.st.NewPickedActor.GetProperty().GetOpacity()
        self.st.iren.Render()


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow(aRenderer)

    sys.exit(app.exec_())
