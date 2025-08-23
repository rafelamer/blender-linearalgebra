# blender-linearalgebra

Aquest repositori conté una llibreria en Python, LinearAlgebra.py, per a 
modelar, representar i animar objectes matemàtics en 3D relacionats amb 
l'Àlgebra Lineal i la Geometria amb el programa [Blender](https://www.blender.org/).

Tal com es pot veure a la [Viquipèdia](https://ca.wikipedia.org/wiki/Blender),
Blender és un programari lliure i gratuït dedicat a l'edició tridimensional sota llicència GNU GPL.
És multiplataforma, empra OpenGL i Vulkan per a la interfície gràfica i està escrit en C, C++ i Python.
És desenvolupat per la Fundació Blender i una àmplia comunitat de voluntaris i inclou eines per al modelatge en 3D, 
l'edició i la texturització de materials, la il·luminació i el render, l'animació d'objectes i personatges, 
els efectes visuals, la composició per nodes, la simulació de fluids i partícules, eines 2D en l'espai 3D.

Algunes funcions de la llibreria *LinearAlgebra.py* fan servir la llibreria de Python [Sympy](https://www.sympy.org).
Si *Sympy* no està instal·lada, aquestes funcions fallaran. 

## Instal·lació de Blender

Per a utilitzar la llibreria *LinearAlgebra*, el primer pas és instal·lar Blender. 

### Linux

Si utilitzeu Linux, el més senzill és instal·lar Blender amb l'eina pròpia de la vostra distribució. Per exemple,
en Fedora, heu d'executar 
```
sudo dnf install blender
```
i, si feu servir Ubuntu o Debian,
```
sudo apt install blender
```

El Blender fa servir Python i, en Linux, fa servir la instal·lació per defecte del sistema i, per a instal·lar
la llibreria *Sympy*, només cal que fem
```
sudo dnf install python3-sympy
```
o
```
sudo apt install python3-sympy
```

### Windows o MacOS

Si utilitzer Windows o MacOS, us heu de descarregar el programa d'instal·lació des de la web de 
[Blender](https://www.blender.org/download/). La versió actual és la 4.5.2. Un cop descarregat, cal
procedir amb la manera habitual d'instal·lació de programes per a Windows o MacOS.

El Blender per a Windows o MacOS porta integrat el Python, per tant, no cal una instal·lació apart. 
Per exemple, en Windows, el Python incorporat a Blender està instal·lat a la carpeta
```
C:\Program Files\Blender Foundation\Blender 4.5\4.5\python
```

Aleshores hem d'instal·lar el *Sympy* al Python que porta integrat el Blender. Per això, obrirem un intèrpret 
de comandes **CMD** o **Símbolo de sistema** com a administrador i executarem el següent:
```
cd "C:\Program Files\Blender Foundation\Blender 4.5\4.5\python"
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py 
.\bin\python.exe get-pip.py 
.\Scripts\pip3.exe install sympy
```

## Instal·lació de LinearAlgebra.py

Podeu trobar tota la informació d'aquesta llibreria al repositori de Github 
[LinearAlgebra](https://github.com/rafelamer/blender-linearalgebra). La manera més senzilla d'obtenir tots
els fitxers del repositori és descarregar-se un fitxer compromit 
[linearalgebra-main.zip](https://github.com/rafelamer/blender-linearalgebra/archive/refs/heads/main.zip).



