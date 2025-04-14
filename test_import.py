try:
    import shotgun_api3
    print('shotgun_api3 version:', shotgun_api3.__version__)
except Exception as e:
    print('Error:', e)