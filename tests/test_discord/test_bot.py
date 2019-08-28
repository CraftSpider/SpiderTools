

def test_extension_load(testbot):

    testbot.load_extensions(testbot.startup_extensions)

    assert len(testbot.extensions) == len(testbot.startup_extensions), "Didn't load all extensions"
    for extension in testbot.startup_extensions:
        assert testbot.extension_dir + "." + extension in testbot.extensions,\
            "Didn't load {} extension".format(extension)

    testbot.unload_extensions(["extension1", "extension0"])

    testbot.unload_extensions()
    assert len(testbot.extensions) == 0, "Didn't unload all extensions"
    for extension in testbot.startup_extensions:
        assert testbot.extension_dir + "." + extension not in testbot.extensions,\
            "Didn't unload {} extension".format(extension)
