#!/usr/bin/env python3

import os
import time
import logging
import gluster.cli
import kubernetes
import openshift.dynamic
import prometheus_client
import urllib3

# [{
#           'name': image['dockerImageReference'],
#           'id': image['metadata']['name'],
#           'digest': layer['name'], #.split(':')[-1],
#           'size': layer['size'],
#           'created': image['metadata']['creationTimestamp'],
#         } for image in images['items'] if image.get('dockerImageLayers') for layer in image['dockerImageLayers']]

BRICKS_NUM = prometheus_client.Gauge('gluster_volume_bricks_num', 'Total number of bricks of Gluster volume', labelnames=['gluster_name', 'kubernetes_namespace', 'kubernetes_name'])
BRICKS_ONLINE = prometheus_client.Gauge('gluster_volume_bricks_online', 'Number of online bricks of Gluster volume', labelnames=['gluster_name', 'kubernetes_namespace', 'kubernetes_name'])

def collect_gluster_metrics():
    volume_status = gluster.cli.volume.status_detail()
    logging.info(f"Collecting gluster metrics, {len(volume_status)} gluster volumes, {len(pvcs)} pvcs")
    for volume in volume_status:
        # heal_info = gluster.cli.heal.info(volume['name'])
        # nr_entries = sum(int(brick['nr_entries']) for brick in heal_info)
        # print(nr_entries)
        gluster_name = volume['name']
        pvc = pvcs.get(volume['name'], {})
        pvc_namespace = pvc.get('namespace', "")
        pvc_name = pvc.get('name', "")
        BRICKS_NUM.labels(volume['name'], pvc_namespace, pvc_name).set(volume['num_bricks'])
        BRICKS_ONLINE.labels(volume['name'], pvc_namespace, pvc_name).set(len([brick for brick in volume['bricks'] if brick['online']]))

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

    # Disable SSL warnings: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
    urllib3.disable_warnings()

    if 'KUBERNETES_PORT' in os.environ:
        kubernetes.config.load_incluster_config()
    else:
        kubernetes.config.load_kube_config()
    k8s_client = kubernetes.client.api_client.ApiClient(kubernetes.client.Configuration())
    dyn_client = openshift.dynamic.DynamicClient(k8s_client)

    v1_persistent_volume = dyn_client.resources.get(api_version='v1', kind='PersistentVolume')

    interval = int(os.getenv('GLUSTER_METRICS_INTERVAL', '300'))
    prometheus_client.start_http_server(8080)
    while True:
        try:
            pvs = v1_persistent_volume.get().items
            for pv in pvs:
                if pv.spec.glusterfs:
                    pvcs = {pv['spec']['glusterfs']['path']:{'namespace': pv['spec']['claimRef']['namespace'], 'name': pv['spec']['claimRef']['name']}}
                    collect_gluster_metrics()
        except Exception as e:
                logging.exception(e)
        time.sleep(interval)
