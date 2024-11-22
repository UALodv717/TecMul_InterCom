import re
import os

dirIn = os.getcwd()+"/texts/in"
dirOut = os.getcwd()+"/texts/out"
fileOut = "datos"
diogenes = False

files = [];#Lista con todos los archivos .txt de la carpeta
allData = [];#Lista con los diccionaros con la informacion obtenida
#Modelo usado para almacenar la info de los archivos, es decir q,w,e,skbps,rkbps,rmse1,rmse2
fileDataModel = {'q':None,'w':None,'e':None,'skbps':None,'rkbps':None,'rmse1':None,'rmse2':None}

shorting = False
#Recomended: ["w","e","q"] --> wavelet, leves, cuants
shortPrio = ["w","e","q"]

#Este script no esta completo pero tiene el minimo funcional, aun me queda: testear la ordenacion,añadir parametos y refactorizar

def getFileData(file):
    
    fileReader = open(dirIn + "/" + file,'r')
    fileData = fileDataModel.copy()
    
    for linea in fileReader:

        #Obtener q
        fileData["q"] = re.search(r"-q\s+(\d+)",linea).group(1) if fileData["q"]==None else fileData["q"] 
        #Obtener w
        fileData["w"] = re.search(r"-w\s+(\w+)",linea).group(1) if fileData["w"]==None else fileData["w"] 
        #Obtener e
        fileData["e"] = re.search(r"-e\s+(\d+)",linea).group(1) if fileData["e"]==None else fileData["e"] 
        #Obtener skbps
        fileData["skbps"] = re.search( r"Payload sent average =\s+(\d+\.\d+)",linea) if fileData["skbps"]==None else fileData["skbps"]
        if isinstance(fileData["skbps"], re.Match):
           fileData["skbps"] = fileData["skbps"].group(1)
        #Obtener rkbps
        fileData["rkbps"] = re.search( r"Payload received average =\s+(\d+\.\d+)",linea) if fileData["rkbps"]==None else fileData["rkbps"] 
        if isinstance(fileData["rkbps"], re.Match):
            fileData["rkbps"] = fileData["rkbps"].group(1)
        #Obtener rmse1
        fileData["rmse1"] = re.search(r"Average RMSE \(Root Mean Square Error\) per sample =\s+\[(\d+\.\d+)",linea) if fileData["rmse1"]==None else fileData["rmse1"]
        if isinstance(fileData["rmse1"], re.Match):
            fileData["rmse1"] = fileData["rmse1"].group(1)
        #Obtener rmse2
        if isinstance(fileData["rmse1"], str):
            fileData["rmse2"] = re.search(r"Average RMSE \(Root Mean Square Error\) per sample = \[" + fileData["rmse1"] + r"\s+(\d+\.\d+)",linea) if fileData["rmse2"]==None else fileData["rmse2"]
            if isinstance(fileData["rmse2"], re.Match):
                fileData["rmse2"] = fileData["rmse2"].group(1)

    #Cerrar 
    fileReader.close()
    allData.append(fileData);
    

def printFile():

    if shorting:
            match len(shortPrio):

                case 1:

                    allData.sort(key=lambda x: (x[shortPrio[0]]))
                case 2:

                    allData.sort(key=lambda x: (x[shortPrio[0]], x[shortPrio[1]]))
                case _:

                    allData.sort(key=lambda x: (x[shortPrio[0]], x[shortPrio[1]],x[shortPrio[2]]))         


    fileOutComplete = fileOut
    iteracionesDeDiogenes=1
    while diogenes & os.path.exists(dirOut+"/"+fileOutComplete+".csv"):
        fileOutComplete = fileOut + str(iteracionesDeDiogenes)
        iteracionesDeDiogenes += 1

    fileOutComplete += ".csv"
    with open(dirOut + "/" + fileOutComplete, 'w') as fo:
        fo.write("archivo;q;w;e;skbps;rkbps;rmse1;rmse2;rmseMed \n")
        indice = 0
        for dic in allData:
            fo.write(files[indice] + ";"
                     + str( dic["q"]) + ";"
                     + str( dic["w"]) + ";"
                     + str( dic["e"]) + ";"
                     + str( dic["skbps"]) + ";"
                     + str( dic["rkbps"]) + ";"
                     + str( dic["rmse1"]) + ";"
                     + str (dic["rmse2"]) + ";"
                     + str( ((float( dic["rmse1"])+float( dic["rmse2"]))/2)) 
                     + "\n") 
            indice+=1
    fo.close()

def getFiles():
     for file in os.listdir(dirIn):
        if file.endswith('.txt'):
            files.append(file)


#set up
getFiles()
print(f"Tratando { len(files) } archivos \n")
print(f"Carpeta de entrada: { dirIn } ")
print(f"Carpeta de salida: { dirOut } ")

if(shorting):
    match len(shortPrio):
        case 1:
            print(f"Ordenacion: Con 1 key: {shortPrio[0]}")
        case 2:
            print(f"Ordenacion: Con 2 keys: {shortPrio[0]} y {shortPrio[1]}")
        case 3:
            print(f"Ordenacion: Con 3 keys: {shortPrio[0]}, {shortPrio[1]} y {shortPrio[2]}")
        case _:
            print(f"Ordenacion: Con 3 keys: {shortPrio[0]}, {shortPrio[1]} y {shortPrio[2]}, el resto han sido ignoradas")

else:
    print("Ordenacion: No")

#core
for file in files:
    getFileData(file)


printFile()
#fin
print(f"\nLa tarea ha terminado con {len(allData)} archivos examinados")
