import pyblish.api


class CollectRenderInstances(pyblish.api.InstancePlugin):
    """ Marks instance to be rendered locally or on the farm

    """
    order = pyblish.api.CollectorOrder
    hosts = ["unreal"]
    families = ["render"]
    label = "Collect Render Instances"

    def process(self, instance):
        self.log.debug("Preparing Rendering Instances")

        render_target = (instance.data["creator_attributes"].
                         get("render_target"))
        if render_target == "farm":
            instance.data["families"].append("render.farm")
            instance.data["farm"] = True
        else:
            instance.data["families"].append("render.local")
