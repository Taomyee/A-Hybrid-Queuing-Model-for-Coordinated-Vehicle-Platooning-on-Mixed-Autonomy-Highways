import numpy as np

def random_experiment(seed):

	with open("data/hello.sumocfg", "w") as routes:
		print("""<?xml version="1.0" encoding="UTF-8"?>
	<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
	<input>
	<net-file value="hello.net.xml"/>
		<route-files value="hello.rou.xml"/>
		<gui-settings-file value="hello.settings.xml"/>
		<seed value="%i"/>
		<no-warnings value="True"/>
	</input>
	<output>
		<tripinfo-output value="trip_info.xml"/>
	</output>
	<time>
		<begin value="0"/>
		<end value="7200"/>
		<step-length value="0.1"/> 
	</time>
	<processing>
		<collision.action value = "none" />
		<lateral-resolution value = "3.2" />
		<!--collision.stoptime value = "3.0" /-->
		<time-to-teleport value = "1000"/>
	</processing>   
</configuration>"""%(seed),file=routes)