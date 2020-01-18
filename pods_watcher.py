# -*- coding: utf-8 -*-

import kubernetes as k8s


def print_pods():

    api = k8s.client.CoreV1Api()
    # return all pods
    ret_obj = api.list_pod_for_all_namespaces(watch=False)
    # print pod information
    print("%15s\t%15s\t%30s" % ("POD IP", "NAMESPACE", "NAME"))
    for pod in ret_obj.items:
        print("%15s\t%15s\t%30s" % (pod.status.pod_ip, pod.metadata.namespace, pod.metadata.name))

def watch_pods(timeout=120):
    """Notice when pod created & deleted

    Keyword Arguments:
        timeout {int} -- how long watch k8s status (default: {120})
    """
    # dictionary of type-message pair
    watch_type = {'ADDED': 'Hello',
                  'DELETED': 'Good bye'}
    api = k8s.client.CoreV1Api()
    watcher = k8s.watch.Watch()
    stream = watcher.stream(api.list_pod_for_all_namespaces, timeout_seconds=timeout)
    for raw_event in stream:
        if raw_event['type'] in watch_type.keys():
            print('%s, %s' % (watch_type[raw_event['type']], raw_event['object'].metadata.name))


if __name__ == "__main__":
    # get kubernetes config
    k8s.config.load_kube_config()
    # print every pod in k8s cluster
    # print_pods()
    # watch and notice pods status
    watch_pods(300)
