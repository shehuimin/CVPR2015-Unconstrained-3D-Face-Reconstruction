# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 13:58:38 2016

@author: hks
"""
import copy
import OBJ
import pickle
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import lsqr,spsolve
import os
from PIL import Image,ImageDraw

def getM(template, pSet, imgSetDir):
    M = []
    X = np.array(template.v)
    Xh = np.c_[X, np.ones((len(X),1))]
    imgList = os.listdir(imgSetDir)
    for (p, imgName) in zip(pSet, imgList):
        imgPath = os.path.join(imgSetDir, imgName)
        im = np.array(Image.open(imgPath).convert('L'))
        proPts = np.round(map(lambda x:np.dot(p, x), Xh))[:,:2]
        tempM = map(lambda x:im[x[1], x[0]], proPts)
        M.append(tempM)
    return np.array(M, dtype = np.float)
    
def getNorm(template, M):
    vNum = len(template.v)
    imgNum = len(M)
    iniN = np.c_[np.ones((vNum, 1)), np.array(template.vn)].T
    #iniL = M.dot(np.linalg.pinv(iniN))
    Norm = iniN
    #L = iniL
    rho = np.ones((imgNum, vNum))
    for i in range(3):
        (rho, L) = updateLP(M, Norm, rho)
        #Norm = np.linalg.lstsq(L, M/rho)[0]
        #productRL = matrixL(L, vNum, imgNum).dot(matrixRho(rho[0]))
        #vecNorm = computeN(productRL, M, Norm)
        #vecNorm = lsqr(productRL, matrix2vector(M))[0]
        #Norm = vecNorm.reshape((4,vecNorm.size/4))
        Norm = computeN2(L, rho, M)
        print np.linalg.norm(M-rho*L.dot(Norm))
        print ('{} times'.format(i))
        
    return Norm

def computeN2(L, rho, M):
    R = M/rho
    Rc = R - np.repeat(L[:,:1], len(M.T), axis=1)
    N = np.linalg.lstsq(L[:,1:], Rc)[0]
    return np.c_[np.ones((len(M.T), 1)), np.array(N.T)].T


def computeN(productRL, M, N):
    lam = 10
    left = productRL.T.dot(productRL) + lam*csr_matrix(np.eye(productRL.shape[1]))
    right = productRL.T.dot(matrix2vector(M)) + lam*matrix2vector(N)
    return spsolve(left, right)

def matrix2vector(matrix):
    return matrix.reshape((matrix.size,1))

def matrixRho(rho):
    rhoRepeat = np.repeat(rho, 4)
    return csr_matrix(np.diag(tuple(rhoRepeat)))

def matrixL(l, vNum, imgNum):
    matrixL = np.zeros((imgNum*vNum, 4*vNum))
    for i in range(imgNum):
        for j in range(vNum):
            matrixL[vNum*i+j,4*j:4*j+4] = l[i]
    return csr_matrix(matrixL)
    
def updateRho(M, l, N):
    rhoVal = M/(l.dot(N))
    meanRho = np.mean(rhoVal, axis = 0)
    
    for i,val in enumerate(meanRho):
        if val < 0:
            meanRho[i] = 0.01
        if val > 2:
            meanRho[i] = 2
    
    meanRho = meanRho.reshape(meanRho.size, 1)
    rho = (np.repeat(meanRho, len(M), axis = 1)).T
    return rho

def updateRho2(M, l, N):
    R = l.dot(N)
    pointNum = len(M.T)
    rhoOne = np.zeros((pointNum, 1))
    for i in range(pointNum):
        rhoOne[i] = np.inner(M[:,i],R[:,i])/np.inner(R[:,i],R[:,i])
    rho = (np.repeat(rhoOne, len(M), axis = 1)).T
    return rho

#更新L跟Rho
def updateLP(M, Norm, rho):
    for i in range(3):
        #L = (M/rho).dot(np.linalg.pinv(N))
        L = (np.linalg.lstsq((Norm*rho[:4,:]).T, (M).T)[0]).T
        print np.linalg.norm(M-rho*(L.dot(Norm)))         
        rho = updateRho2(M, L, Norm)
        #rho = M/(L.dot(N))
        print np.linalg.norm(M-rho*(L.dot(Norm)))
    return rho, L

def drawNorm(imgPath, template, Norm, P):
    radius = 1
    img = Image.open(imgPath)
    imDraw = ImageDraw.Draw(img)
    V = template.v
    for (point, n) in zip(V, Norm):
        point2D = P.dot(np.r_[point,[1]])[:2]
        point2DP = P.dot(np.r_[point + n,[1]])[:2]
        imDraw.line((tuple(point2D.astype(int)), tuple(point2DP.astype(int))),fill = 'red')
        imDraw.ellipse((point2DP[0]-radius, point2DP[1]-radius, point2DP[0]+radius, point2DP[1]+radius), fill = 'black')
    return img

"""
LxT = L.dot(X0).reshape((19802,3))
ans = []
for (l, n) in zip(a2, oriNorm):
    l = l/np.linalg.norm(l)
    ans.append(np.dot(l, n)/np.linalg.norm(l))
"""
if __name__ == '__main__':
    pSet = pickle.load(open(r'D:\WinPython-64bit-2.7.10.1\mine\Unconstrained 3D Face Reconstruction\data\warpData3\pMatrix','r'))
    imgSetDir = r'D:\WinPython-64bit-2.7.10.1\mine\Unconstrained 3D Face Reconstruction\data\warpData3\xi'
    template = OBJ.obj(r'D:\WinPython-64bit-2.7.10.1\mine\Unconstrained 3D Face Reconstruction\data\warpData3\warp.obj')
    #template = OBJ.obj(r'D:\WinPython-64bit-2.7.10.1\mine\Unconstrained 3D Face Reconstruction\data\ballCut2.obj')
    template.load()
    temp = copy.deepcopy(template)
    vCount = len(template.v)
    M = getM(template, pSet[:-1], imgSetDir)
    oriNorm1 = np.array(template.vn)
    Norm = getNorm(template, M)
    oriNorm = Norm[1:].T
    oriNormN = (np.array(map(np.linalg.norm, oriNorm))).reshape((vCount,1))
    oriNorm = oriNorm/oriNormN
    L = computeL(template)
    #LPlus = np.r_[np.ones((3,3*vCount)),L]
    X0 = np.array(template.v).reshape((3*vCount,1))
    X = X0
    for i in range(3):
        Lx = L.dot(X)
        Lx = Lx.reshape((len(Lx)/3,3))
        
        H = []
        for (h, no) in zip(Lx, oriNorm):
            hN = h.dot(no)/np.linalg.norm(h)
            if hN > 0:
                if hN < np.cos(np.pi*1/3):
                    H.append(h)
                else:
                    H.append(np.linalg.norm(h)*no)
            else:
                if hN < np.cos(np.pi*1/3):
                    H.append(h)
                else:
                    H.append(-np.linalg.norm(h)*no)
        right = np.array(H).reshape((3*vCount,1))
        
                #H.append(np.linalg.norm(h))
        #H = np.array(H).repeat(3).reshape((3*(vCount), 1))
        #right = L.dot(X0)
        #xx = spsolve(L, H*oriNorm.reshape((oriNorm.size,1)))
        #right = -H*oriNorm.reshape((oriNorm.size,1))
       # right = -H*Norm[1:].T.reshape((Norm[1:].size,1))
        #right = H*np.ones((16722,1))
        #rightP = np.r_[np.zeros((3,1)),right]
        xx = lsqr(L, right)[0]
        #xx = inv(L.T.dot(L)).dot(L.T).dot(b)
        temp.v = xx.reshape((vCount,3))
        temp.save(r'D:\WinPython-64bit-2.7.10.1\mine\Unconstrained 3D Face Reconstruction\data\tempResult\normRec{}.obj'.format(i))
        X = xx
    
    
    
    