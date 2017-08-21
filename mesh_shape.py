import bpy
from enum import Enum

class Gradient(Enum):
    BlackToWhite = 0
    WhiteToBlack = 1
    Alpha = 2

class GenerateType(Enum):
    Depth = 0
    Outline = 1

class Side(Enum):
        Front = 0
        Left = 1
        Back = 2
        Right = 3
        Top = 4
        Bottom = 5

class Pixel():
    def __init__(self, X, Y, Z):
        self.X = X
        self.Y = Y
        self.Z = Z

class MeshShape():
    def __init__(self, GradientType, MeshMaxDepth, GenerateType, Image):
        self.Pixels = list(Image.pixels)
        self.GradientType = GradientType
        self.ImageWidth = Image.size[0]
        self.ImageHeight = Image.size[1]
        self.MaxDepth = MeshMaxDepth
        
        self.Mesh = bpy.data.meshes.new("ImageMesh")
        self.Object = bpy.data.objects.new("ImageObject", self.Mesh)
        
        scn = bpy.context.scene
        scn.objects.link(self.Object)
        scn.objects.active = self.Object
        self.Object.select = True
        
        self.Verts = []
        self.VertEdges = []
        self.VertIndices = []
        
        if GenerateType == GenerateType.Depth:
            self.__CreateDepthMesh()
            self.Mesh.from_pydata(self.Verts, [], self.VertIndices)
        elif GenerateType == GenerateType.Outline:
            self.__CreateOutlineMesh()
            self.Mesh.from_pydata(self.Verts, self.VertEdges, [])
        
        self.Mesh.update()
    
    def __IgnoreColor(self, RGBA):
        if self.GradientType == Gradient.BlackToWhite:
            return RGBA[:3] == [1.0, 1.0, 1.0]
        if self.GradientType == Gradient.WhiteToBlack:
            return RGBA[:3] == [0.0, 0.0, 0.0]
        if self.GradientType == Gradient.Alpha:
            return RGBA[3] == 0.0
    
    def __CalculateZ(self, RGBA):
        if self.GradientType == Gradient.BlackToWhite:
            return (((1.0 - RGBA[0]) + (1.0 - RGBA[1]) + (1.0 - RGBA[2])) / 3.0) * -self.MaxDepth
        if self.GradientType == Gradient.WhiteToBlack:
            return ((RGBA[0] + RGBA[1] + RGBA[2]) / 3.0) * -self.MaxDepth
        if self.GradientType == Gradient.Alpha:
            return RGBA[3] * -self.MaxDepth
    
    def __ContainsPosition(self, X, Y):
        if X >= 0 and X < self.ImageWidth and Y >= 0 and Y < self.ImageHeight:
            i = ((Y * self.ImageWidth) + X) * 4 #Multiply by 4 because the pixel array is an RGBA array
            if i >= 0 and i < len(self.Pixels):
                if not self.__IgnoreColor(self.Pixels[i:i+4]):
                    return i
        return -1
    
    def __PixelDepthAt(self, X, Y):
        i = self.__ContainsPosition(X, Y)
        if i != -1:
            return self.__CalculateZ(self.Pixels[i:i+4])
        return None
    
    def __CreateDepthMesh(self):
        CurrentVerts = {} #Dictionary of dictionaries containing indexes of verts
        VertCount = 0
        for Y in range(self.ImageHeight, -1, -1):
            for X in range(self.ImageWidth):
                CurrentPixel = Pixel(X, Y, self.__PixelDepthAt(X, Y))
                BottomPixel = Pixel(X, Y - 1, self.__PixelDepthAt(X, Y - 1))
                RightPixel = Pixel(X + 1, Y, self.__PixelDepthAt(X + 1, Y))
                BottomRightPixel = Pixel(X + 1, Y - 1, self.__PixelDepthAt(X + 1, Y - 1))
                BottomLeftPixel = Pixel(X - 1, Y - 1, self.__PixelDepthAt(X - 1, Y - 1))
                
                #Create top left tri
                TopLeftCreated = self.__CreateTri(CurrentPixel, BottomPixel, RightPixel, CurrentVerts)
                
                if not TopLeftCreated:
                    #Create bottom left tri
                    self.__CreateTri(CurrentPixel, BottomPixel, BottomRightPixel, CurrentVerts)
                    #Create top right tri
                    self.__CreateTri(CurrentPixel, BottomRightPixel, RightPixel, CurrentVerts)
                
                #Create bottom right tri
                self.__CreateTri(CurrentPixel, BottomLeftPixel, BottomPixel, CurrentVerts)
    
    #Returns the index of the vert at X Y
    def __AddVertIfNotAdded(self, X, Y, Z, CurrentVerts):
        if Y not in CurrentVerts:
            CurrentVerts[Y] = {}
        
        if X not in CurrentVerts[Y]:
            VertCount = len(self.Verts)
            CurrentVerts[Y][X] = VertCount
            self.Verts.append((X, Z, Y))
            return VertCount
        else:
            return CurrentVerts[Y][X]
    
    #Returns true if tri was created
    def __CreateTri(self, FirstPixel, SecondPixel, ThirdPixel, CurrentVerts):
        if FirstPixel.Z != None and SecondPixel.Z != None and ThirdPixel.Z != None:
            FirstIndex = self.__AddVertIfNotAdded(FirstPixel.X, FirstPixel.Y, FirstPixel.Z, CurrentVerts)
            SecondIndex = self.__AddVertIfNotAdded(SecondPixel.X, SecondPixel.Y, SecondPixel.Z, CurrentVerts)
            ThirdIndex = self.__AddVertIfNotAdded(ThirdPixel.X, ThirdPixel.Y, ThirdPixel.Z, CurrentVerts)
            
            self.VertIndices.append((FirstIndex, SecondIndex, ThirdIndex))
            
            return True
        return False
    
    def __NextClockwiseDir(self, DirX, DirY):
        NewDirX = DirX + DirY
        if NewDirX == 2:
            NewDirX = 1
        elif NewDirX == -2:
            NewDirX = -1
        
        NewDirY = DirY - DirX
        if NewDirY == 2:
            NewDirY = 1
        elif NewDirY == -2:
            NewDirY = -1
        
        return NewDirX, NewDirY
    
    def __SuitableForClockwise(self, X, Y, IgnorePixel):
        i = self.__ContainsPosition(X, Y)
        
        if i == -1:
            return False
        
        AdjacentCount = 0
        DirectionX = 0
        DirectionY = 1
        for i in range(8):
            if self.__ContainsPosition(X + DirectionX, Y + DirectionY) != -1:
                AdjacentCount += 1
            DirectionX, DirectionY = self.__NextClockwiseDir(DirectionX, DirectionY)
        
        if AdjacentCount > 1:
            return True
        
        return False
    
    #Also returns the direction from the next pixel to X Y
    def __NextClockwisePixel(self, X, Y, DirectionX, DirectionY, IgnorePixel):
        for i in range(8):
            if self.__ContainsPosition(X + DirectionX, Y + DirectionY) != -1:
                return X + DirectionX, Y + DirectionY, -DirectionX, -DirectionY
            DirectionX, DirectionY = self.__NextClockwiseDir(DirectionX, DirectionY)
        
        return None
    
    def __CreateOutlineMesh(self):
        StartX = 0
        StartY = self.ImageHeight - 1
        while True:
            if self.__ContainsPosition(StartX, StartY) != -1:
                break
            else:
                StartX += 1
                if StartX == self.ImageWidth:
                    StartX = 0
                    StartY -= 1
                if StartY == -1:
                    break
        
        AddedVerts = {}
        VertEdgeIndex = 0
        DirectionX = 0
        DirectionY = 1 #Start clockwise from 12 o'clock
        X, Y, DirectionX, DirectionY = self.__NextClockwisePixel(StartX, StartY, DirectionX, DirectionY, Pixel(-1, -1, -1))
        Previous = Pixel(StartX, StartY, 0)
        self.Count = 0
        TotalPixels = len(self.Pixels) // 4
        while (X != StartX or Y != StartY) and self.Count < TotalPixels:
            AddedNewVert = self.__AddVertIfNotAdded(Previous.X, Previous.Y, 0, AddedVerts) == (len(self.Verts) - 1)
            if AddedNewVert:
                self.VertEdges.append([VertEdgeIndex, VertEdgeIndex + 1])
                VertEdgeIndex += 1
            PrevX = X
            PrevY = Y
            DirectionX, DirectionY = self.__NextClockwiseDir(DirectionX, DirectionY)
            X, Y, DirectionX, DirectionY = self.__NextClockwisePixel(X, Y, DirectionX, DirectionY, Previous)
            Previous.X = PrevX
            Previous.Y = PrevY
            self.Count += 1
        
        self.Verts.append((Previous.X, 0, Previous.Y))
        self.VertEdges.append([VertEdgeIndex, 0])
    
    #Adds edges to the end of existing verts
    def __AddEdge(self, SideFirst, SideSecond, FirstVertSide, SecondVertSide):
        for i in range(len(SideFirst.Edges[FirstVertSide])):
            X, Y = SideFirst.Edges[FirstVertSide][i]
            
            Z = 0
            
            if FirstVertSide == Side.Right or FirstVertSide == Side.Left:
                Z = -SideSecond.GetXInEdge(Y, SecondVertSide) + SideSecond.MaxWidth
            else:
                Z = SideSecond.GetYInEdge(X, SecondVertSide)
            
            self.Verts.append((X, Z, Y))
            self.VertEdges.append([self.VertEdgeIndex, self.VertEdgeIndex + 1])
            self.VertEdgeIndex += 1
    
    def __ConvertXYZ(self, XYZ, ToSide):
        if ToSide == Side.Top or ToSide == Side.Bottom:
            return XYZ[1], XYZ[0], XYZ[2] #Swap X and Y
        
        return XYZ[0], XYZ[1], XYZ[2]
    
    def __SetCornerIndexes(self, Index, XY, Shape, ShapeSide):
        if self.CornerIndexes[ShapeSide][0] == -1:
            if XY == Shape.TopRightPixel():
                self.CornerIndexes[ShapeSide][0] = Index #Top right corner
                self.CurrentVertSide = Side.Right
        
        if self.CornerIndexes[ShapeSide][1] == -1:
            if XY == Shape.BottomRightPixel():
                self.CornerIndexes[ShapeSide][1] = Index #Bottom right corner
                self.CurrentVertSide = Side.Bottom
        
        if self.CornerIndexes[ShapeSide][2] == -1:
            if XY == Shape.BottomLeftPixel():
                self.CornerIndexes[ShapeSide][2] = Index #Bottom left corner
                self.CurrentVertSide = Side.Left
        
        if self.CornerIndexes[ShapeSide][3] == -1:
            if XY == Shape.TopLeftPixel():
                self.CornerIndexes[ShapeSide][3] = Index #Top left corner
                self.CurrentVertSide = Side.Top
    
    def __SideFromIndex(self, VertIndex, FaceSide):
        Corners = self.CornerIndexes[FaceSide]
        ReturnSide = Side.Right
        
        if Corners[1] != -1:
            if VertIndex >= Corners[1]:
                ReturnSide = Side.Bottom
        
        if Corners[2] != -1:
            if VertIndex >= Corners[2]:
                ReturnSide = Side.Left
        
        if Corners[3] != -1:
            if VertIndex >= Corners[3]:
                ReturnSide = Side.Top
        
        return ReturnSide
