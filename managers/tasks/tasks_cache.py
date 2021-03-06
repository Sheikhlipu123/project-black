import json
from datetime import datetime

from black.db import Sessions, TaskDatabase
from managers.tasks.shadow_task import ShadowTask

from common.logger import log


@log
class TasksCache:
    def __init__(self):
        self.active = dict()
        self.finished = dict()

        self.session_manager = Sessions()

        self._restore_tasks_from_db()

    def _restore_tasks_from_db(self):
        with self.session_manager.get_session() as session:
            tasks_from_db = session.query(TaskDatabase).all()
            tasks = list(map(lambda x:
                            ShadowTask(task_id=x.task_id,
                                        task_type=x.task_type,
                                        target=json.loads(x.target),
                                        params=json.loads(x.params),
                                        project_uuid=x.project_uuid,
                                        status=x.status,
                                        progress=x.progress,
                                        text=x.text,
                                        date_added=x.date_added,
                                        date_finished=x.date_finished,
                                        stdout=x.stdout,
                                        stderr=x.stderr),
                            tasks_from_db))

        for task in tasks:
            status = task.get_status()[0]
            if status == 'Aborted' or status == 'Finished':
                self.finished[task.task_id] = task
            else:
                self.active[task.task_id] = task

    def get_fresh_active(self, project_uuid, update_fresh=False):
        tasks = (
            list(filter(
                lambda task: task.fresh and (
                    project_uuid is None or
                    task.project_uuid == project_uuid
                ),
                self._get_active_tasks()
            ))
        )

        # for task in self._get_active_tasks():
        #     print(task.progress, task.project_uuid, project_uuid, task.fresh)

        if update_fresh:
            for task in tasks:
                task.set_fresh(False)

        return tasks

    def get_fresh_finished(self, project_uuid, update_fresh=False):
        tasks = (
            list(filter(
                lambda task: task.fresh and (
                    project_uuid is None or
                    task.project_uuid == project_uuid
                ),
                self._get_finished_tasks()
            ))
        )

        if update_fresh:
            for task in tasks:
                task.set_fresh(False)

        return tasks

    def get_active(self, project_uuid):
        return (
            list(filter(
                lambda task: (
                    project_uuid is None or
                    task.project_uuid == project_uuid
                ),
                self._get_active_tasks()
            ))
        )

    def get_finished(self, project_uuid):
        return (
            list(filter(
                lambda task: (
                    project_uuid is None or
                    task.project_uuid == project_uuid
                ),
                self._get_finished_tasks()
            ))
        )

    def _get_active_tasks(self):
        return self.active.values()

    def _get_finished_tasks(self):
        return self.finished.values()

    def add_tasks(self, tasks):
        for task in tasks:
            self.active[task.task_id] = task

    def update_task(self, body):
        task_id = body['task_id']
        new_status = body['status']
        new_progress = body['progress']
        new_text = body['text']
        new_stdout = body['new_stdout']
        new_stderr = body['new_stderr']

        task = self.active.get(task_id, None)
        if task is None:
            self.logger.error("The task id {} is not in cache".format(task_id))

            return

        if new_status != task.status or new_progress != task.progress:
            task.set_fresh(True)

            self.logger.debug(
                "Task {} updated. {}->{}, {}->{}".format(
                    task.task_id,
                    task.status, new_status,
                    task.progress, new_progress
                )
            )

        task.set_status(new_status, new_progress, new_text, new_stdout, new_stderr)

        if task.quitted():
            self.handle_quitted(task)

        return task

    def handle_quitted(self, task):
        self.finished[task.task_id] = task
        task.date_finished = datetime.utcnow()
        task.fresh = True
        del self.active[task.task_id]

    def get_active_task(self, task_id):
        return self.active.get(task_id, None)

    def cancel(self, task_id):
        task = self.get_active_task(task_id)

        if task:
            self.handle_quitted(task)
