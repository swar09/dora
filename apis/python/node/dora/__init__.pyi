import typing

import pyarrow

import dora

@typing.final
class Enum:
    """Create a collection of name/value pairs.

    Example enumeration:

    >>> class Color(Enum):
    ...     RED = 1
    ...     BLUE = 2
    ...     GREEN = 3

    Access them by:

    - attribute access:

    >>> Color.RED
    <Color.RED: 1>

    - value lookup:

    >>> Color(1)
    <Color.RED: 1>

    - name lookup:

    >>> Color['RED']
    <Color.RED: 1>

    Enumerations can be iterated over, and know how many members they have:

    >>> len(Color)
    3

    >>> list(Color)
    [<Color.RED: 1>, <Color.BLUE: 2>, <Color.GREEN: 3>]

    Methods can be added to enumerations, and members can have their own
    attributes -- see the documentation for details.
    """

    @staticmethod
    def __contains__(value: typing.Any) -> bool:
        """
        Check whether a value is an enum member or equals one of the enum member values.
        
        `value` is considered contained if it is a member of the enum class or if it equals the value of any member.
        
        Returns:
            `True` if `value` is an enum member or equals a member's value, `False` otherwise.
        """

    @staticmethod
    def __getitem__(name: typing.Any) -> typing.Any:
        """
        Return the enum member with the given name.
        
        Parameters:
            name (Any): The member name to look up.
        
        Returns:
            Any: The enum member matching `name`.
        """

    @staticmethod
    def __iter__() -> typing.Any:
        """Return members in definition order."""

    @staticmethod
    def __len__() -> int:
        """Return the number of members (no aliases)"""

@typing.final
class Node:
    """The custom node API lets you integrate `dora` into your application.
    It allows you to retrieve input and send output in any fashion you want.

    Use with:

    ```python
    from dora import Node

    node = Node()
    ```
    """

    def __init__(self, node_id: str = None) -> None:
        """
        Create a Node instance for integrating dora into an application.
        
        Parameters:
            node_id (str): Optional node identifier; if omitted, a default identifier is assigned.
        """

    def dataflow_descriptor(self) -> dict:
        """
        Get the parsed dataflow YAML descriptor for this node's dataflow.
        
        Returns:
            descriptor (dict): The full dataflow descriptor as a dictionary parsed from the node's dataflow YAML.
        """

    def dataflow_id(self) -> str:
        """
        Get the identifier of the dataflow associated with this node.
        
        Returns:
            dataflow_id (str): The unique identifier of the dataflow.
        """

    def merge_external_events(self, subscription: dora.Ros2Subscription) -> None:
        """
        Merge an external ROS2 subscription into this node's event stream.
        
        Parameters:
            subscription (dora.Ros2Subscription): ROS2 subscription whose incoming events will be integrated into the node's main event loop and become available via this node's `next`, `recv_async`, and iteration APIs.
        """

    def next(self, timeout: float = None) -> dict:
        """
        Retrieve the next input event received by the node, blocking until an event is available or the optional timeout elapses.
        
        Parameters:
        	timeout (float): Maximum time in seconds to wait for an event; if omitted, wait indefinitely.
        
        Returns:
        	dict: The next event dictionary, or `None` when all senders have been dropped.
        """

    def node_config(self) -> dict:
        """
        Retrieve this node's configuration as defined in the dataflow descriptor.
        
        Returns:
            dict: A mapping containing this node's configuration values parsed from the dataflow (keys are configuration names).
        """

    def recv_async(self, timeout: float = None) -> dict:
        """
        Retrieve the next input event without blocking until one becomes available.
        
        Parameters:
            timeout (float, optional): Maximum time in seconds to wait for an event before returning an Error. If omitted, returns immediately with an available event or `None`/Error as described below.
        
        Returns:
            dict: The next received input event.
            `None` if all senders have been dropped.
            An Error object if the timeout is reached.
        
        Warning:
            This feature is experimental due to ongoing development of the pyo3 async (Rust-Python FFI) integration.
        """

    def send_output(
        self, output_id: str, data: pyarrow.Array, metadata: dict = None
    ) -> None:
        """
        Send data to the node's specified output.
        
        Parameters:
            output_id (str): Identifier of the node output to send the data to.
            data (pyarrow.Array): Arrow array containing the output payload; must conform to the expected output schema.
            metadata (dict, optional): Optional metadata associated with the output (for example, tracing or telemetry context).
        """

    def __iter__(self) -> typing.Any:
        """
        Iterate over the node's incoming event stream.
        
        Returns:
        	An iterator that yields received input event dictionaries; iteration ends when all senders are dropped.
        """

    def __next__(self) -> typing.Any:
        """Implement next(self)."""

    def __repr__(self) -> str:
        """Return repr(self)."""

    def __str__(self) -> str:
        """Return str(self)."""

@typing.final
class Ros2Context:
    """ROS2 Context holding all messages definition for receiving and sending messages to ROS2.

    By default, Ros2Context will use env `AMENT_PREFIX_PATH` to search for message definition.

    AMENT_PREFIX_PATH folder structure should be the following:

    - For messages: <namespace>/msg/<name>.msg
    - For services: <namespace>/srv/<name>.srv

    You can also use `ros_paths` if you don't want to use env variable.

    warning::
    dora Ros2 bridge functionality is considered **unstable**. It may be changed
    at any point without it being considered a breaking change.

    ```python
    context = Ros2Context()
    ```
    """

    def __init__(self, ros_paths: typing.List[str] = None) -> None:
        """
        Create a ROS2 context that loads ROS message and service definitions for use with ROS2 nodes.
        
        By default, the context discovers message and service definitions using the AMENT_PREFIX_PATH environment variable. Expected layout under each prefix:
        - messages: <namespace>/msg/<name>.msg
        - services: <namespace>/srv/<name>.srv
        
        Parameters:
            ros_paths (List[str], optional): Explicit list of filesystem paths to search for ROS definitions. If omitted, AMENT_PREFIX_PATH is used.
        
        Warnings:
            The dora ROS2 bridge is considered unstable and its API or behavior may change without a breaking-release guarantee.
        
        Example:
            context = Ros2Context()
        """

    def new_node(
        self, name: str, namespace: str, options: dora.Ros2NodeOptions
    ) -> dora.Ros2Node:
        """
        Create a new ROS2 node with the given name, namespace, and options.
        
        Parameters:
            name (str): Node name.
            namespace (str): Node namespace.
            options (dora.Ros2NodeOptions): Configuration options for the node.
        
        Returns:
            dora.Ros2Node: The created ROS2 node.
        
        Warnings:
            The dora ROS2 bridge functionality is considered unstable and may change at any time without a breaking-change guarantee.
        """

    def __repr__(self) -> str:
        """
        Return a string representation of the object suitable for debugging.
        
        Returns:
            repr_str (str): The object's canonical representation, preferably a valid Python expression that can be used to recreate the object when possible.
        """

    def __str__(self) -> str:
        """Return str(self)."""

@typing.final
class Ros2Durability:
    """DDS 2.2.3.4 DURABILITY"""

    def __eq__(self, value: typing.Any) -> bool:
        """Return self==value."""

    def __ge__(self, value: typing.Any) -> bool:
        """Return self>=value."""

    def __gt__(self, value: typing.Any) -> bool:
        """Return self>value."""

    def __int__(self) -> None:
        """int(self)"""

    def __le__(self, value: typing.Any) -> bool:
        """Return self<=value."""

    def __lt__(self, value: typing.Any) -> bool:
        """Return self<value."""

    def __ne__(self, value: typing.Any) -> bool:
        """Return self!=value."""

    def __repr__(self) -> str:
        """Return repr(self)."""

    def __str__(self) -> str:
        """Return str(self)."""

@typing.final
class Ros2Liveliness:
    """DDS 2.2.3.11 LIVELINESS"""

    def __eq__(self, value: typing.Any) -> bool:
        """Return self==value."""

    def __ge__(self, value: typing.Any) -> bool:
        """Return self>=value."""

    def __gt__(self, value: typing.Any) -> bool:
        """Return self>value."""

    def __int__(self) -> None:
        """int(self)"""

    def __le__(self, value: typing.Any) -> bool:
        """Return self<=value."""

    def __lt__(self, value: typing.Any) -> bool:
        """Return self<value."""

    def __ne__(self, value: typing.Any) -> bool:
        """Return self!=value."""

    def __repr__(self) -> str:
        """Return repr(self)."""

    def __str__(self) -> str:
        """Return str(self)."""

@typing.final
class Ros2Node:
    """ROS2 Node

    warnings::
    - dora Ros2 bridge functionality is considered **unstable**. It may be changed
    at any point without it being considered a breaking change.
    - There's a known issue about ROS2 nodes not being discoverable by ROS2
    See: https://github.com/jhelovuo/ros2-client/issues/4
    """

    def create_publisher(
        self, topic: dora.Ros2Topic, qos: dora.Ros2QosPolicies = None
    ) -> dora.Ros2Publisher:
        """
        Create a ROS2 publisher for a given topic.
        
        Warning:
            dora ROS2 bridge functionality is considered unstable and may change.
        
        Parameters:
            topic (dora.Ros2Topic): Topic descriptor to publish to.
            qos (dora.Ros2QosPolicies, optional): Quality-of-Service policies for the publisher; if omitted a default QoS is used.
        
        Returns:
            dora.Ros2Publisher: Publisher instance bound to the specified topic.
        """

    def create_subscription(
        self, topic: dora.Ros2Topic, qos: dora.Ros2QosPolicies = None
    ) -> dora.Ros2Subscription:
        """
        Create a ROS2 subscription for a topic.
        
        Parameters:
            topic (dora.Ros2Topic): Topic descriptor to subscribe to.
            qos (dora.Ros2QosPolicies, optional): Quality-of-service settings to apply to the subscription.
        
        Returns:
            dora.Ros2Subscription: A subscription object that provides received messages for the topic.
        
        Warnings:
            dora ROS2 bridge functionality is considered unstable and may change without a breaking-change guarantee.
        """

    def create_topic(
        self, name: str, message_type: str, qos: dora.Ros2QosPolicies
    ) -> dora.Ros2Topic:
        """
        Create a ROS2 topic descriptor for a given topic name and message type.
        
        Parameters:
            name (str): Full topic name (for example, "/turtle1/cmd_vel").
            message_type (str): ROS2 message type string in the form "package/Message" (for example, "geometry_msgs/Twist").
            qos (dora.Ros2QosPolicies): Quality-of-Service policies to apply to the topic.
        
        Returns:
            dora.Ros2Topic: An object representing the created ROS2 topic.
        """

    def __repr__(self) -> str:
        """
        Return a string representation of the object suitable for debugging.
        
        Returns:
            repr_str (str): The object's canonical representation, preferably a valid Python expression that can be used to recreate the object when possible.
        """

    def __str__(self) -> str:
        """Return str(self)."""

@typing.final
class Ros2NodeOptions:
    """ROS2 Node Options"""

    def __init__(self, rosout: bool = None) -> None:
        """ROS2 Node Options"""

    def __repr__(self) -> str:
        """Return repr(self)."""

    def __str__(self) -> str:
        """Return str(self)."""

@typing.final
class Ros2Publisher:
    """ROS2 Publisher

    Warnings:
    - dora Ros2 bridge functionality is considered **unstable**. It may be changed
    at any point without it being considered a breaking change.

    """

    def publish(self, data: pyarrow.Array) -> None:
        """
        Publish a ROS2 message represented as a PyArrow Array.
        
        Parameters:
            data (pyarrow.Array): Arrow array whose record/struct layout matches the ROS2 message schema published by this publisher.
        """

    def __repr__(self) -> str:
        """
        Return a string representation of the object suitable for debugging.
        
        Returns:
            repr_str (str): The object's canonical representation, preferably a valid Python expression that can be used to recreate the object when possible.
        """

    def __str__(self) -> str:
        """Return str(self)."""

@typing.final
class Ros2QosPolicies:
    """ROS2 QoS Policy"""

    def __init__(
        self,
        durability: dora.Ros2Durability = None,
        liveliness: dora.Ros2Liveliness = None,
        reliable: bool = None,
        keep_all: bool = None,
        lease_duration: float = None,
        max_blocking_time: float = None,
        keep_last: int = None,
    ) -> dora.Ros2QosPolicies:
        """ROS2 QoS Policy"""

    def __repr__(self) -> str:
        """Return repr(self)."""

    def __str__(self) -> str:
        """Return str(self)."""

@typing.final
class Ros2Subscription:
    """ROS2 Subscription

    Warnings:
    - dora Ros2 bridge functionality is considered **unstable**. It may be changed
    at any point without it being considered a breaking change.

    """

    def next(self): """
Wait for and return the next received input event.

Returns:
    event (dict): The next input event as a dictionary, or `None` if all senders have been dropped.
"""
...
    def __repr__(self) -> str:
        """
        Return a string representation of the object suitable for debugging.
        
        Returns:
            repr_str (str): The object's canonical representation, preferably a valid Python expression that can be used to recreate the object when possible.
        """

    def __str__(self) -> str:
        """Return str(self)."""

@typing.final
class Ros2Topic:
    """ROS2 Topic

    Warnings:
    - dora Ros2 bridge functionality is considered **unstable**. It may be changed
    at any point without it being considered a breaking change.

    """

    def __repr__(self) -> str:
        """
        Return a string representation of the object suitable for debugging.
        
        Returns:
            repr_str (str): The object's canonical representation, preferably a valid Python expression that can be used to recreate the object when possible.
        """

    def __str__(self) -> str:
        """Return str(self)."""

def build(
    dataflow_path: str,
    uv: bool = None,
    coordinator_addr: str = None,
    coordinator_port: int = None,
    force_local: bool = False,
) -> None:
    """Build a Dataflow, exactly the same way as `dora build` command line tool."""

def run(dataflow_path: str, uv: bool = None, stop_after: float = None) -> None:
    """
    Run a dataflow using the same behavior as the `dora run` CLI.
    
    Parameters:
        dataflow_path (str): Path to the dataflow YAML file.
        uv (bool, optional): Enable UV for running Python nodes.
        stop_after (float, optional): Automatically stop the dataflow after this many seconds.
    """

def start_runtime() -> None:
    """
    Start the operator runtime.
    
    Initializes and runs the runtime responsible for executing Operators defined by a dataflow.
    """
