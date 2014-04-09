from __future__ import division
from collections import Counter

import numpy as np

# data es un dataframe que tiene que contener una columna class. La cual el arbol intenta predecir.
# podria pensar en relajar esto y simplemente indicar cual es la variable a predecir.

class Node:
    def __init__(self, data, level = 1, max_depth = 8, min_samples_split=10):

        # Atributos particulares del nodo
        self.data = data
        self.is_leaf = False
        self.clase = ''
        self.feat_name = ""
        self.feat_value = None
        self.left = None
        self.right = None
        self.entropia = self.entropy(data)
        self.is_left = False
        self.is_right = False
        self.level = level

        # Atributos generales del arbol
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split

        # Si es necesario particionar el nodo, llamo a split para hacerlo
        if self.check_data():
            self.split()

            # Falta corregir esto. No entiendo pq a veces el split deja el feat_name como vacio
            if self.feat_name != '':
                print 'Feature elegida: ' + self.feat_name
                menores = self.data[self.data[self.feat_name] < self.feat_value]
                mayores = self.data[self.data[self.feat_name] >= self.feat_value]

                if not menores.empty:
                    self.add_left(menores)
                if not mayores.empty:
                    self.add_right(mayores)

            else:
                self.set_leaf()

        # De lo contrario llamo a set_leaf para transformarlo en hoja
        else:
            self.set_leaf()

    # Busca el mejor corte posible para el nodo
    def split(self):
        # Inicializo la ganancia de info en el peor nivel posible
        max_gain = -float('inf')

        # Para cada feature (no considero la clase ni la completitud)
        filterfeatures = self.filterfeatures()

        print filterfeatures

        for f in filterfeatures:
            print 'Evaluando feature: ' + f

            # separo el dominio en todas las posibles divisiones para obtener la division optima
            pivotes = self.get_pivotes(self.data[f], 'exact')
            # pivotes = self.get_pivotes(self.data[f], 'aprox')

            for pivote in pivotes:

                # Separo las tuplas segun si su valor de esa variable es menor o mayor que el pivote
                menores = self.data[self.data[f] < pivote]
                mayores = self.data[self.data[f] >= pivote]

                # No considero caso en que todos los datos se vayan a una sola rama
                if menores.empty or mayores.empty:
                    continue

                # Calculo la ganancia de informacion para esta variable
                gain = self.gain(menores, mayores, f)

                # Comparo con la ganancia anterior, si es mejor guardo el gain, la feature correspondiente y el pivote
                if (gain > max_gain):
                    max_gain = gain
                    self.feat_name = f
                    self.feat_value = pivote

    # Retorna las features a considerar en un nodo para hacer la particion
    def filterfeatures(self):
        return [f for f in self.data.columns if not '_comp' in f and f is not 'class']


    # determina se es necesario hacer un split de los datos
    def check_data(self):
        featuresfaltantes = self.filterfeatures()

        if self.data['class'].nunique() == 1 or len(featuresfaltantes) == 0:
            return False
        elif self.level >= self.max_depth:
            return False
        elif self.data.shape[0] < self.min_samples_split:
            return False
        else:
            return True

    # retorna una lista con los todos los threshold a evaluar para buscar la mejor separacion
    def get_pivotes(self, feature, calidad = 'exact'):

        if calidad == 'exact':
            return feature[1:].unique()
        elif calidad == 'aprox':
            minimo = feature.min()
            maximo = feature.max()
            step = maximo - minimo / 100
            pivotes = []
            for i in range(100):
                pivotes.append(minimo + step*i)

            return pivotes

    # Convierte el nodo en hoja. Colocando la clase mas probable como resultado
    def set_leaf(self):
        self.is_leaf = True
        # self.clase = stats.mode(self.data['class'])[0].item()
        aux = Counter(self.data['class'])
        self.clase = aux.most_common(1)[0][0]
        

    def add_left(self, left_data):
        self.left = self.__class__(left_data, self.level+1, self.max_depth, self.min_samples_split)
        self.left.is_left = True

    def add_right(self, right_data):
        self.right = self.__class__(right_data, self.level+1, self.max_depth, self.min_samples_split)
        self.right.is_right = True

    def predict(self, tupla, confianza=1):
        if self.is_leaf:
            return self.clase, confianza
        else:
            if tupla[self.feat_name] < self.feat_value:
                return self.left.predict(tupla)
            else:
                return self.right.predict(tupla)

    def show(self, linea=""):
        if self.is_leaf:
            print linea + '|---- ' + str(self.clase)

        elif self.is_left:
            self.right.show(linea + '|     ')
            print linea + '|- '+ self.feat_name + ' ' + '(' + ("%.2f" % self.feat_value) + ')'
            self.left.show(linea + '      ')

        elif self.is_right:
            self.right.show(linea + '      ')
            print linea + '|- ' + self.feat_name + ' ' + '(' + ("%.2f" % self.feat_value) + ')'
            self.left.show(linea + '|     ')

        # Es el nodo raiz
        else:
            self.right.show(linea + '      ')
            print linea + '|- '+ self.feat_name + ' ' + '(' + ("%.2f" % self.feat_value) + ')'
            self.left.show(linea + '      ')  

    
    # Retorna la ganancia de dividir los datos en menores y mayores.
    # Deje la variable feature que no me sirve en la clase base, solo para ahorrarme repetir el metodo split. 
    # Eso debe poder arreglarse
    def gain(self, menores, mayores, feature):

        total = len(self.data.index)

        gain = self.entropia - (len(menores) * self.entropy(menores) + len(mayores) * self.entropy(mayores)) / total

        return gain

    # Retorna la entropia de un grupo de datos
    def entropy(self, data):
        clases = data['class'].unique()
        total = len(data.index)

        entropia = 0

        for c in clases:
            p_c = len(data[data['class'] == c].index) / total
            entropia -= p_c * np.log2(p_c)

        return entropia