import luigi
from exasol_integration_test_docker_environment.lib.base.docker_base_task import DockerBaseTask
from exasol_integration_test_docker_environment.lib.config.docker_config import target_docker_repository_config
from exasol_integration_test_docker_environment.lib.docker.images.utils import find_images_by_tag


class CleanImageTask(DockerBaseTask):
    jobid = luigi.Parameter("")
    image_id = luigi.Parameter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run_task(self):
        self.logger.info("Try to remove dependent images of %s" % self.image_id)
        yield from self.run_dependencies(self.get_clean_image_tasks_for_dependent_images())
        for i in range(3):
            try:
                self.logger.info("Try to remove image %s" % self.image_id)
                self._client.images.remove(image=self.image_id, force=True)
                self.logger.info("Removed image %s" % self.image_id)
                break
            except Exception as e:
                self.logger.info("Could not removed image %s got exception %s" % (self.image_id, e))

    def get_clean_image_tasks_for_dependent_images(self):
        image_ids = [str(possible_child).replace("sha256:", "") for possible_child
                     in self._low_level_client.images(all=True, quiet=True)
                     if self.is_child_image(possible_child)]
        return [self.create_child_task(CleanImageTask, image_id=image_id)
                for image_id in image_ids]

    def is_child_image(self, possible_child):
        try:
            inspect = self._low_level_client.inspect_image(image=str(possible_child).replace("sha256:", ""))
            return str(inspect["Parent"]).replace("sha256:", "") == self.image_id
        except:
            return False


class CleanImagesStartingWith(DockerBaseTask):

    jobid = luigi.Parameter("")
    starts_with_pattern = luigi.Parameter()

    def register_required(self):
        image_ids = [str(image.id).replace("sha256:", "")
                     for image in self.find_images_to_clean()]
        self.register_dependencies([self.create_child_task(CleanImageTask, image_id=image_id)
                                    for image_id in image_ids])

    def find_images_to_clean(self):
        self.logger.info("Going to remove all images starting with %s" % self.starts_with_pattern)
        filter_images = find_images_by_tag(self._client, lambda tag: tag.startswith(self.starts_with_pattern))
        for i in filter_images:
            self.logger.info("Going to remove following image: %s" % i.tags)
        return filter_images

    def run_task(self):
        pass
