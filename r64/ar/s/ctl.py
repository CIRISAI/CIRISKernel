exec(open(__file__.replace("ctl.py","lib.py")).read())
run("control room of seven", ROOM)
run("honest five remove G at aG", ROOM+[remove("xg","G",FIVE,("aG",))], ids=("xg",))
