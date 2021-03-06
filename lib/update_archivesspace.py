from bhlaspaceapiclient import ASpaceClient
from .utils import parse_deposited_aips_csv


def update_existing_digital_object(aspace, archival_object, handle, unpublish_dos):
    existing_do_updated = False
    dos_without_file_versions = []
    for instance in archival_object.get("instances"):
        if instance["instance_type"] == "digital_object":
            digital_object = aspace.get_aspace_json(instance["digital_object"]["ref"])
            if not digital_object["file_versions"]:
                dos_without_file_versions.append(digital_object)
    if dos_without_file_versions:
        do_to_update = dos_without_file_versions[0]
        do_to_update["file_versions"] = [{
                                        'file_uri': handle,
                                        'xlink_show_attribute': "new",
                                        'xlink_actuate_attribute': "onRequest"
                                        }]
        if unpublish_dos:
            do_to_update["publish"] = False
        else:
            do_to_update["publish"] = True
        aspace.update_aspace_object(do_to_update["uri"], do_to_update)
        existing_do_updated = True
        if len(dos_without_file_versions) > 1:
            dos_to_delete = dos_without_file_versions[1:]
            for do_to_delete in dos_to_delete:
                aspace.delete_aspace_object(do_to_delete["uri"])
    return existing_do_updated


def make_digital_object(title, handle, uuid, unpublish_dos):
    if unpublish_dos:
        publish = False
    else:
        publish = True
    digital_object = {}
    digital_object["title"] = title
    digital_object["digital_object_id"] = uuid
    digital_object["publish"] = publish
    digital_object["file_versions"] = [{
                                    'file_uri': handle,
                                    'xlink_show_attribute': "new",
                                    'xlink_actuate_attribute': "onRequest"
                                    }]
    return digital_object


def make_digital_object_instance(digital_object_uri):
    instance = {'instance_type': 'digital_object',
                'digital_object': {'ref': digital_object_uri}}
    return instance


def update_archivesspace(AIPRepackager):
    deposited_aips = parse_deposited_aips_csv(AIPRepackager)
    aspace = ASpaceClient(AIPRepackager.aspace_instance)
    digital_object_post_uri = aspace.repository + "/digital_objects"
    for aip in deposited_aips:
        print("Updating {}".format(aip["archival_object_uri"]))
        archival_object = aspace.get_aspace_json(aip["archival_object_uri"])
        existing_do_updated = update_existing_digital_object(aspace, archival_object, aip["handle"], AIPRepackager.unpublish_dos)
        if not existing_do_updated:
            title = aspace.make_display_string(archival_object)
            digital_object = make_digital_object(title, aip["handle"], aip["uuid"], AIPRepackager.unpublish_dos)
            response = aspace.post_aspace_json(digital_object_post_uri, digital_object)
            digital_object_uri = response["uri"]
            digital_object_instance = make_digital_object_instance(digital_object_uri)
            archival_object["instances"].append(digital_object_instance)
            aspace.update_aspace_object(archival_object["uri"], archival_object)
