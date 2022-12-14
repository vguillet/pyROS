
from dep.pyROS.src.pyROS.Endpoints.Core.Shared_variable.Shared_variable import Shared_variable


class Shared_variable_module:
    def __init__(self):
        pass

    # ---------------------------------------------- Declaration
    def declare_shared_variable(self,
                                name: str,
                                value: int or float or str or bool = None,
                                descriptor=None,
                                scope="global",
                                variable_type: str = "unspecified",
                                ignore_override: bool = False) -> Shared_variable:
        """
        Declare a shared_variable on the node.

        :param name: The name of the shared_variable.
        :param value: The value of the shared_variable.
        :param descriptor: The descriptor of the shared_variable.
        :param scope: The scope of the shared_variable (global or local).
        :param variable_type: The type of the shared_variable.
        :param ignore_override: If True, ignore any existing shared_variables with the same name.
        """

        # -> Check if shared_variable already declared in this node
        for shared_variable in self.callbackgroups["default_shared_variable_callback_group"].callbacks:
            # -> Return existing shared_variable if name matches and ignore override is False
            if shared_variable.name == name and not ignore_override:
                return shared_variable

            # -> Set the value of the existing shared_variable if name matches and ignore override is True
            elif shared_variable.name == name and ignore_override:
                shared_variable.set_value(value=value)
                return shared_variable

        # -> Create a shared_variable
        new_shared_variable = Shared_variable(
            name=name,
            value=value,
            scope=scope,
            variable_type=variable_type,
            ignore_override=ignore_override,
            parent_node_ref=self.ref)

        # -> Add the shared_variable to the default shared_variable callback group
        self.callbackgroups["default_shared_variable_callback_group"].add_callback(new_shared_variable)

        # -> Return the shared_variable object
        return new_shared_variable

    def declare_shared_variables(self,
                                 shared_variables,
                                 namespace: str = ""):
        """
        Declare multiple shared_variables on the node.

        Each shared_variable is a dictionary with the following keys:
        - name: The name of the shared_variable.
        - value: The value of the shared_variable.
        - scope: The scope of the shared_variable (global or local).
        - variable_type: The type of the shared_variable.
        - ignore_override: If True, ignore any existing shared_variables with the same name.

        :param shared_variables: The list of shared_variables to declare.
        :param namespace: The namespace of the shared_variables.
        """

        # -> Create a list of shared_variables
        new_shared_variables = []
        for shared_variable in shared_variables:
            new_shared_variables.append(
                self.declare_shared_variable(
                    name=namespace + shared_variable["name"],
                    value=shared_variable["value"],
                    scope=shared_variable["scope"],
                    variable_type=shared_variable["variable_type"],
                    ignore_override=shared_variable["ignore_override"])
                )

        # -> Return the list of shared_variables
        return new_shared_variables

    def undeclare_shared_variable(self, name: str) -> None:
        """
        Undeclare a previously declared shared_variable.
        """
        pass

    # ---------------------------------------------- Getters
    def get_shared_variable(self, name: str) -> Shared_variable:
        pass

    def get_shared_variables(self, names):
        pass

    # ---------------------------------------------- Setters
    def set_shared_variable(self, shared_variable: str) -> None:
        pass

    def set_shared_variables(self, shared_variable_list) -> None:
        pass
