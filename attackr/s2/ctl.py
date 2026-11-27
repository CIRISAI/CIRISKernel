exec(open(__file__.replace("ctl.py","lib.py")).read())
run("control", ROOM, ids=("aD","aG"))
run("honest five remove G at aG", ROOM+[remove("xg","G",FIVE,("aG",))], ids=("xg",))
run("two concurrent honest admissions at aG, both signed by A..E (vi)", ROOM+[admit("ah","H",FIVE,("aG",)), admit("aj","J",FIVE,("aG",))], ids=("ah","aj"))
