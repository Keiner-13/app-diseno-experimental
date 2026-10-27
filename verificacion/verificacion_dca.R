datos <- read.csv("../data/dca_mi_variante.csv", stringsAsFactors = FALSE) # Lee los datos propios desde la carpeta data; ejecuta este script desde verificacion/.
datos$secador <- factor(datos$secador) # Indica a R que secador representa grupos de tratamiento y no una cantidad numérica.
modelo_dca <- aov(humedad ~ factor(secador), data = datos) # Ajusta el ANOVA de un factor para comparar las medias de humedad entre secadores.
print(summary(modelo_dca)) # Muestra la tabla ANOVA con la variación atribuible a secadores y al error experimental.
medias_secador <- aggregate(humedad ~ secador, data = datos, FUN = mean) # Calcula la media de humedad observada para cada secador.
print(medias_secador) # Presenta las medias para identificar descriptivamente qué secadores tienen respuestas mayores o menores.
tabla_anova <- summary(modelo_dca)[[1]] # Guarda la tabla ANOVA para extraer el cuadrado medio del error.
cuadrado_medio_error <- tabla_anova["Residuals", "Mean Sq"] # Obtiene el CME, que estima la variabilidad experimental no explicada por los tratamientos.
coeficiente_variacion <- sqrt(cuadrado_medio_error) / mean(datos$humedad) * 100 # Calcula CV = raíz(CME) / media general × 100 para expresar el error relativo en porcentaje.
cat("Coeficiente de variación (CV):", coeficiente_variacion, "%\n") # Imprime el CV para valorar el error experimental respecto a la media de humedad.
print(TukeyHSD(modelo_dca)) # Compara por pares las medias de secador y ajusta la inferencia por comparaciones múltiples.
