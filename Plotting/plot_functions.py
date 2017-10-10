

# Define various functions useful for plotting

def msavi(R, NIR):
    # Modified Soil Adjusted Vegetation Index

    return (2.0 * NIR + 1.0 - ((2.0 * NIR + 1.0) ** 2.0 - 8.0 * (NIR - R)) ** 0.5) / 2.0

def ndvi(R, NIR):
    # Normalized Difference Vegetation Index

    return (NIR - R) / (NIR + R)

def evi(B, R, NIR, G=2.5, L=1.0, C1=6, C2=7.5):
    # Enhanced Vegetation Index

    return G * ((NIR - R) / (NIR + C1 * R - C2 * B + L))

def savi(R, NIR, L=0.5):
    # Soil Adjusted Vegetation Index

    return ((NIR - R) / (NIR + R + L)) * (1 + L)

def ndmi(NIR, SWIR1):
    # Normalized Difference Moisture Index

    return (NIR - SWIR1) / (NIR + SWIR1)

def nbr(NIR, SWIR2):
    # Normalized Burn Ratio

    return (NIR - SWIR2) / (NIR + SWIR2)

def nbr2(SWIR1, SWIR2):
    # Normalized Burn Ratio 2

    return (SWIR1 - SWIR2) / (SWIR1 + SWIR2)
