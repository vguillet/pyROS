
import warnings
from datetime import datetime
import json

from redis_lock import Lock

from dep.pyROS.src.pyROS.Endpoints.Endpoint import Endpoint


class Shared_variable(Endpoint):
    def __init__(self,
                 name: str,
                 value=None,
                 scope: str = "global",
                 variable_type: str = "unspecified",
                 descriptor: str = "",
                 ignore_override: bool = False,
                 parent_node_ref: str = None):
        """
        Create a iteration2 shared_variable endpoint

        :param name: The name of the shared_variable
        :param value: The current value of the shared_variable, can be kept as None if creating a pointer to an existing shared_variable
        :param scope: The scope of the shared_variable, can be "global" or "local"
        :param variable_type: The type of the shared_variable, must be JSON serializable
        :param descriptor: A description of the shared_variable
        :param ignore_override: If True, ignore any existing shared_variables with the same name.

        :param parent_node_ref: The reference of the parent node
        """

        # -> Setup endpoint
        Endpoint.__init__(self, parent_node_ref=parent_node_ref)

        # -> Initialise the shared_variable properties
        if scope == "global":
            self.name = name
        else:
            self.name = self.parent_node_ref + name

        self.scope = scope
        self.variable_type = variable_type
        self.descriptor = descriptor
        self.__value = value
        self.__raw_value = self.__build_value(value=value)  # Raw value format
        self.__cached_value = None                          # Raw value format

        # -> Check whether the shared_variable exists
        if not self.client.exists(self.name) or ignore_override:
            # -> Update the shared_variable shared value
            self.client.set(self.name, json.dumps(self.__raw_value))

        # -> Perform initial spin to get the value if shared_variable already exists
        self.spin()

        # -> Declare the endpoint in the comm graph
        self.declare_endpoint()

    def __build_value(self, value) -> dict:
        value = {
            "timestamp": datetime.timestamp(datetime.now()),
            "variable_type": self.variable_type,
            "descriptor": self.descriptor,
            "parent_node_ref": self.parent_node_ref,
            "setter_ref": self.ref,
            "value": value
        }

        return value

    @property
    def shared_value(self):
        raw_value = self.client.get(self.name)
        raw_value = json.loads(raw_value)

        return raw_value

    def spin(self) -> None:
        """
        Update the value of the shared_variable to the latest value
        """

        # -> Push cached value if it is not None
        with Lock(redis_client=self.client, name=self.ref):
            if self.__cached_value is not None:
                with Lock(redis_client=self.client, name=self.name):
                    # -> Update the shared value with the cached value if the cached value is newer than the shared value
                    if float(self.__cached_value["timestamp"]) > float(self.shared_value["timestamp"]):
                        # -> Update the shared_variable shared value
                        self.client.set(self.name, json.dumps(self.__cached_value))

                        # -> Set local value to cached value
                        self.__raw_value = self.__cached_value
                        self.__value = self.__cached_value["value"]

                        # -> Reset cached value
                        self.__cached_value = None

                        return

                # -> Reset cached value
                self.__cached_value = None

            with Lock(redis_client=self.client, name=self.name):
                # -> Set local value to shared value
                self.__raw_value = self.shared_value
                self.__value = self.shared_value["value"]

    def get_value(self, spin: bool = True):
        """
        Get the value of the shared_variable
        """
        if spin:
            # -> Spin the shared_variable to get the latest value
            self.spin()

        # -> Return the value of the shared_variable
        return self.__value

    def get_raw_value(self, spin: bool = True):
        """
        Get the raw value of the shared_variable
        """
        if spin:
            # -> Spin the shared_variable to get the latest value
            self.spin()

        # -> Return the value of the shared_variable
        return self.__raw_value

    def set_value(self,
                  value,
                  instant: bool = True) -> None:
        """
        Set the value of the shared_variable
        If instant is True, the value will be set immediately, otherwise it will be set at the next spin

        :param value: The value to set the shared_variable to
        :param instant: Whether to set the value immediately or at the next spin
        """

        # -> Check whether the value is of the right type
        if self.variable_type != "unspecified":
            # -> Convert variable type string to type
            if self.variable_type == "int" and not isinstance(value, int):
                warnings.warn(f"Trying to set a value of incorrect type to {self.name} shared_variable, expected int, got {type(value)}")
                return

            elif self.variable_type == "float" and not isinstance(value, float):
                warnings.warn(f"Trying to set a value of incorrect type to {self.name} shared_variable, expected float, got {type(value)}")
                return

            elif self.variable_type == "str" and not isinstance(value, str):
                warnings.warn(f"Trying to set a value of incorrect type to {self.name} shared_variable, expected str, got {type(value)}")
                return

            elif self.variable_type == "bool" and not isinstance(value, bool):
                warnings.warn(f"Trying to set a value of incorrect type to {self.name} shared_variable, expected bool, got {type(value)}")
                return

        # -> Construct the raw value
        new_value = self.__build_value(value=value)

        if instant:
            # -> Update the shared_variable value
            self.client.set(self.name, json.dumps(new_value))

            # -> Cache the cache value
            self.__cached_value = None

        else:
            # -> Set the cached value
            with Lock(redis_client=self.client, name=self.ref):
                self.__cached_value = new_value

    def declare_endpoint(self) -> None:
        with Lock(redis_client=self.client, name="Comm_graph"):
            # -> Get the communication graph from the redis server
            comm_graph = json.loads(self.client.get("Comm_graph"))

            # -> Declare the endpoint in the parent node
            comm_graph[self.parent_node_ref].append(
                {"ref": self.ref,
                 "type": "shared_variable",
                 "name": self.name,
                 "scope": self.scope,
                 "variable_type": self.variable_type,
                 "descriptor": self.descriptor}
            )

            # -> Update comm_graph shared variable
            self.client.set("Comm_graph", json.dumps(comm_graph))

    def destroy_endpoint(self) -> None:
        with Lock(redis_client=self.client, name="Comm_graph"):
            # -> Get the communication graph from the redis server
            comm_graph = json.loads(self.client.get("Comm_graph"))

            # -> Undeclare the endpoint in the parent node
            comm_graph[self.parent_node_ref].remove(
                {"ref": self.ref,
                 "type": "shared_variable",
                 "name": self.name,
                 "scope": self.scope,
                 "variable_type": self.variable_type,
                 "descriptor": self.descriptor}
            )

            # -> Update comm_graph shared variable
            self.client.set("Comm_graph", json.dumps(comm_graph))
