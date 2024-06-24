import requests
import time
import os
import urllib.parse
from prettytable import PrettyTable
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timezone
import json
import concurrent.futures

_ = load_dotenv(override=True)

# Retrieve settings from environment variables
API_KEY = os.getenv('PLUGIN_API_KEY')
ACCOUNT_IDENTIFIER = os.getenv('PLUGIN_ACCOUNT_IDENTIFIER')
ORG_IDENTIFIER = os.getenv('PLUGIN_ORG_IDENTIFIER')
PROJECT_IDENTIFIER = os.getenv('PLUGIN_PROJECT_IDENTIFIER')
PIPELINE_IDENTIFIER = os.getenv('PLUGIN_PIPELINE_IDENTIFIER')
BRANCH = os.getenv('PLUGIN_BRANCH')
REPO_IDENTIFIER = os.getenv('PLUGIN_REPO_IDENTIFIER')
MODULE_TYPE = os.getenv('PLUGIN_MODULE_TYPE')
GET_DEFAULT_FROM_OTHER_REPO = os.getenv('PLUGIN_GET_DEFAULT_FROM_OTHER_REPO', 'true')
USE_FQN_IF_ERROR = os.getenv('PLUGIN_USE_FQN_IF_ERROR', 'false')
NOTIFY_ONLY_USER = os.getenv('PLUGIN_NOTIFY_ONLY_USER', 'false')
NOTES_FOR_PIPELINE_EXECUTION = os.getenv('PLUGIN_NOTES_FOR_PIPELINE_EXECUTION', '')
PIPELINE_YAML = os.getenv('PLUGIN_PIPELINE_YAML')
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

TRIGGER_URL_TEMPLATE = (
    'https://app.harness.io/pipeline/api/pipeline/execute/{pipeline_identifier}'
    '?accountIdentifier={account_identifier}'
    '&orgIdentifier={org_identifier}'
    '&projectIdentifier={project_identifier}'
)

STATUS_URL_TEMPLATE = (
    'https://app.harness.io/pipeline/api/pipelines/execution/v2/{plan_execution_id}'
    '?accountIdentifier={account_identifier}'
    '&orgIdentifier={org_identifier}'
    '&projectIdentifier={project_identifier}'
)

STEP_DETAILS_URL_TEMPLATE = (
    'https://app.harness.io/pipeline/api/pipelines/execution/subGraph/{plan_execution_id}/{node_execution_id}'
    '?accountIdentifier={account_identifier}'
    '&orgIdentifier={org_identifier}'
    '&projectIdentifier={project_identifier}'
)

PIPELINE_URL_TEMPLATE = (
    'https://app.harness.io/pipeline/api/pipelines/execution/url'
    '?accountIdentifier={account_identifier}'
    '&orgIdentifier={org_identifier}'
    '&projectIdentifier={project_identifier}'
    '&pipelineIdentifier={pipeline_identifier}'
    '&planExecutionId={plan_execution_id}'
)

LOG_SERVICE_BASE_URL = 'https://app.harness.io/gateway/log-service/blob'

def debug_print(message):
    if DEBUG_MODE:
        print(message)

def build_trigger_url():
    url = TRIGGER_URL_TEMPLATE.format(
        pipeline_identifier=PIPELINE_IDENTIFIER,
        account_identifier=ACCOUNT_IDENTIFIER,
        org_identifier=ORG_IDENTIFIER,
        project_identifier=PROJECT_IDENTIFIER
    )
    if MODULE_TYPE:
        url += f'&moduleType={MODULE_TYPE}'
    if BRANCH:
        url += f'&branch={BRANCH}'
    if REPO_IDENTIFIER:
        url += f'&repoIdentifier={REPO_IDENTIFIER}'
    if GET_DEFAULT_FROM_OTHER_REPO:
        url += f'&getDefaultFromOtherRepo={GET_DEFAULT_FROM_OTHER_REPO}'
    if USE_FQN_IF_ERROR:
        url += f'&useFQNIfError={USE_FQN_IF_ERROR}'
    if NOTIFY_ONLY_USER:
        url += f'&notifyOnlyUser={NOTIFY_ONLY_USER}'
    if NOTES_FOR_PIPELINE_EXECUTION:
        url += f'&notesForPipelineExecution={NOTES_FOR_PIPELINE_EXECUTION}'
    
    return url

def format_pipeline_yaml(yaml_content):
    if '\\n' in yaml_content:
        # Convert single line with \n to actual multiline string
        yaml_content = yaml_content.replace('\\n', '\n')
    return yaml_content

def trigger_pipeline():
    url = build_trigger_url()
    
    headers = {
        'Content-Type': 'application/yaml',
        'x-api-key': 'API_KEY'
    }
    
    formatted_yaml = format_pipeline_yaml(PIPELINE_YAML)
    
    response = requests.post(url, headers=headers, data=formatted_yaml)
    return response.json()

def get_execution_status(plan_execution_id):
    url = STATUS_URL_TEMPLATE.format(
        plan_execution_id=plan_execution_id,
        account_identifier=ACCOUNT_IDENTIFIER,
        org_identifier=ORG_IDENTIFIER,
        project_identifier=PROJECT_IDENTIFIER
    )
    
    headers = {
        'x-api-key': API_KEY
    }
    
    response = requests.get(url, headers=headers)
    return response.json()

def get_step_details(plan_execution_id, node_execution_id):
    url = STEP_DETAILS_URL_TEMPLATE.format(
        plan_execution_id=plan_execution_id,
        node_execution_id=node_execution_id,
        account_identifier=ACCOUNT_IDENTIFIER,
        org_identifier=ORG_IDENTIFIER,
        project_identifier=PROJECT_IDENTIFIER
    )
    
    headers = {
        'x-api-key': API_KEY
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and 'data' in response.json():
        return response.json()['data']['executionGraph']['nodeMap']
    return None

def get_pipeline_url(plan_execution_id):
    url = PIPELINE_URL_TEMPLATE.format(
        account_identifier=ACCOUNT_IDENTIFIER,
        org_identifier=ORG_IDENTIFIER,
        project_identifier=PROJECT_IDENTIFIER,
        pipeline_identifier=PIPELINE_IDENTIFIER,
        plan_execution_id=plan_execution_id
    )
    
    headers = {
        'x-api-key': API_KEY
    }
    
    response = requests.post(url, headers=headers)
    if response.status_code == 200 and 'data' in response.json():
        return response.json()['data']
    return None

def print_header():
    print("=============================================")
    print("           Harness Trigger Automation Plugin")
    print("=============================================")
    print()
    
    table = PrettyTable()
    table.field_names = ["Parameter", "Value"]
    table.add_row(["API Key", "********"])
    table.add_row(["Account Identifier", ACCOUNT_IDENTIFIER])
    table.add_row(["Org Identifier", ORG_IDENTIFIER])
    table.add_row(["Project Identifier", PROJECT_IDENTIFIER])
    table.add_row(["Pipeline Identifier", PIPELINE_IDENTIFIER])
    table.add_row(["Branch", BRANCH])
    table.add_row(["Repo Identifier", REPO_IDENTIFIER])
    table.add_row(["Module Type", MODULE_TYPE])
    table.add_row(["Get Default From Other Repo", GET_DEFAULT_FROM_OTHER_REPO])
    table.add_row(["Use FQN If Error", USE_FQN_IF_ERROR])
    table.add_row(["Notify Only User", NOTIFY_ONLY_USER])
    table.add_row(["Notes For Pipeline Execution", NOTES_FOR_PIPELINE_EXECUTION])
    print(table)
    print()

def convert_to_human_readable(timestamp):
    if timestamp:
        return datetime.fromtimestamp(timestamp / 1000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    return 'N/A'

def convert_to_human_readable_time(iso_time):
    dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
    return dt.strftime('%Y-%m-%d %H:%M:%S UTC')

def get_pipeline_execution_json(execution_id, routing_id, org_identifier, project_identifier, account_identifier, authorization_token, stage_node_id):
    url = f'https://app.harness.io/gateway/pipeline/api/pipelines/execution/v2/{execution_id}?routingId={routing_id}&orgIdentifier={org_identifier}&projectIdentifier={project_identifier}&accountIdentifier={account_identifier}&stageNodeId={stage_node_id}'
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7,es-419;q=0.6,es;q=0.5',
        'x-api-key': f'{authorization_token}',
        'priority': 'u=1, i',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        debug_print("Success getting pipeline execution")
        return response.json()
    else:
        raise Exception(f"Failed to retrieve pipeline execution JSON. Status code: {response.status_code}, Response: {response.text}")

def get_log_token(routing_id, account_id, authorization_token):
    url = f'https://app.harness.io/gateway/log-service/token?routingId={routing_id}&accountID={account_id}'
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7,es-419;q=0.6,es;q=0.5',
        'x-api-key': f'{authorization_token}',
        'priority': 'u=1, i'
    }

    debug_print(f"Requesting log token with headers: {headers}")
    debug_print(f"Request URL: {url}")
    response = requests.get(url, headers=headers)
    debug_print(f"Response status code: {response.status_code}, Response text: {response.text}")

    if response.status_code == 200:
        return response.text.strip()
    else:
        raise Exception(f"Failed to retrieve log token. Status code: {response.status_code}, Response: {response.text}")


def extract_log_keys(node_info):
    log_keys = []
    if 'logBaseKey' in node_info:
        log_keys.append(node_info['logBaseKey'])
    if 'executableResponses' in node_info:
        for executable_response in node_info['executableResponses']:
            if 'logKeys' in executable_response:
                log_keys.extend(executable_response['logKeys'])
            elif 'task' in executable_response and 'logKeys' in executable_response['task']:
                log_keys.extend(executable_response['task']['logKeys'])
            elif 'taskChain' in executable_response and 'logKeys' in executable_response['taskChain']:
                log_keys.extend(executable_response['taskChain']['logKeys'])
            elif 'children' in executable_response and 'logKeys' in executable_response['children']:
                log_keys.extend(executable_response['children']['logKeys'])
    return log_keys

def fetch_log(url, headers):
    response = requests.get(url, headers=headers)
    return response

def get_logs_from_json(json_data, authorization_token, account_identifier, stage_name):
    debug_print("Getting logs")
    account_id = account_identifier
    routing_id = account_identifier
    log_token = get_log_token(
        routing_id=routing_id,
        account_id=account_id,
        authorization_token=authorization_token
    )

    base_url = LOG_SERVICE_BASE_URL
    org_id = json_data['data']['pipelineExecutionSummary']['orgIdentifier']
    project_id = json_data['data']['pipelineExecutionSummary']['projectIdentifier']
    pipeline_id = json_data['data']['pipelineExecutionSummary']['pipelineIdentifier']
    run_sequence = json_data['data']['pipelineExecutionSummary']['runSequence']

    debug_print(f"base_url: {base_url}")

    headers = {
        'accept': '*/*',
        'x-api-key': f'{authorization_token}',
        'content-type': 'application/json',
        'x-harness-token': log_token,
        'accept-language': 'en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7,es-419;q=0.6,es;q=0.5',
        'priority': 'u=1, i',
        'referer': f'https://app.harness.io/ng/account/{account_id}/module/cd/orgs/{org_id}/projects/{project_id}/pipelines/{pipeline_id}/executions/{run_sequence}/pipeline?storeType=INLINE',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }

    logs = []

    if 'executionGraph' not in json_data['data'] or 'nodeMap' not in json_data['data']['executionGraph']:
        raise KeyError("'executionGraph' or 'nodeMap' key not found in the JSON data")

    node_map = json_data['data']['executionGraph']['nodeMap']
    
    shown_logs = set()
    log_urls = []
    for node_id, node_info in node_map.items():
        debug_print(f"NodeID: {node_id}")
        debug_print(f"NodeInfo: {node_info}")
        if node_info.get('stepType', '') == 'Background':
            debug_print(f"Skipping Background step: {node_info['name']}")
            continue

        step_name = node_info.get('name', 'Unknown Step')
        timeout = node_info.get('stepParameters', {}).get('timeout', 'N/A')

        log_keys = extract_log_keys(node_info)

        for log_key in log_keys:
            encoded_log_key = urllib.parse.quote(log_key)
            url = f'{base_url}?accountID={account_id}&orgId={org_id}&pipelineId={pipeline_id}&projectId={project_id}&key={encoded_log_key}'
            log_urls.append((url, step_name, timeout, stage_name))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(fetch_log, url, headers): (url, step_name, timeout, stage_name) for url, step_name, timeout, stage_name in log_urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url, step_name, timeout, stage_name = future_to_url[future]
            response = future.result()
            debug_print(f"Log fetch response status: {response.status_code}, response text: {response.text[:100]}")
            if response.status_code == 200:
                try:
                    log_content = response.json()
                    debug_print(f"Log Success 200 for {stage_name}\n {log_content}")
                    if isinstance(log_content, list):
                        for log_entry in log_content:
                            if isinstance(log_entry, dict) and log_entry.get('out', '') not in shown_logs:
                                human_readable_time = convert_to_human_readable_time(log_entry.get('time', ''))
                                log_line = {
                                    'stage': stage_name,
                                    'step': step_name,
                                    'timeout': timeout,
                                    'time': human_readable_time,
                                    'out': log_entry.get('out', '')
                                }
                                print(log_line)
                                logs.append(log_line)
                                shown_logs.add(log_entry.get('out', ''))
                    elif isinstance(log_content, dict):
                        for key, log_entry in log_content.items():
                            if isinstance(log_entry, dict) and log_entry.get('out', '') not in shown_logs:
                                human_readable_time = convert_to_human_readable_time(log_entry.get('time', ''))
                                log_line = {
                                    'stage': stage_name,
                                    'step': step_name,
                                    'timeout': timeout,
                                    'time': human_readable_time,
                                    'out': log_entry.get('out', '')
                                }
                                print(log_line)
                                logs.append(log_line)
                                shown_logs.add(log_entry.get('out', ''))
                    else:
                        debug_print(f"Unexpected log_content type: {type(log_content)}")
                except ValueError:
                    log_content = response.text
                    if log_content not in shown_logs:
                        logs.append({
                            'stage': stage_name,
                            'step': step_name,
                            'timeout': timeout,
                            'log': log_content
                        })
                        debug_print(f"Failed to parse JSON response for log key {log_key}. Storing as text.")
                        shown_logs.add(log_content)
            else:
                debug_print(f"Failed to fetch logs for {url}. Status code: {response.status_code}, Response: {response.text}")

    return logs

def monitor_pipeline(plan_execution_id, debug=False):
    last_status = {}
    completed = False
    stage_logs = {}
    while not completed:
        status_response = get_execution_status(plan_execution_id)
        summary = status_response['data']['pipelineExecutionSummary']
        status = summary['status']
        failure_message = summary.get('failureInfo', {}).get('message', '')
        stage_status = summary['layoutNodeMap']
        pipeline_url = get_pipeline_url(plan_execution_id)

        stages = []
        for stage_id, stage_details in stage_status.items():
            debug_print(f"Stage ID: {stage_id}")
            if stage_details['status'] in ['Running', 'Success', 'Failed', 'Errored', 'Paused', 'Stopped']:
                stages.append({
                    'name': stage_details['name'],
                    'status': stage_details['status'],
                    'startTs': stage_details.get('startTs', 0),
                    'endTs': stage_details.get('endTs', 0),
                    'nodeExecutionId': stage_details['nodeExecutionId'],
                    'nodePlanId': stage_id,
                    'failureMessage': stage_details.get('failureInfo', {}).get('message', '')
                })
        
        stages.sort(key=lambda x: x['startTs'])
        changes = []

        if pipeline_url and last_status.get("pipeline_url") != pipeline_url:
            changes.append(f"Pipeline URL: {pipeline_url}")
            last_status["pipeline_url"] = pipeline_url

        if last_status.get("pipeline_status") != status:
            changes.append(f"Pipeline Status: {status}")
            last_status["pipeline_status"] = status

        if failure_message and last_status.get("pipeline_failure_message") != failure_message:
            table = PrettyTable()
            table.field_names = ["Scope", "Message"]
            table.add_row(["Pipeline", failure_message])
            changes.append(table.get_string())
            last_status["pipeline_failure_message"] = failure_message

        for stage in stages:
            debug_print("Checking stage changes")
            debug_print(f"stage: {stage}")

            stage_key = f"{stage['name']}_{stage['status']}"
            start_time = convert_to_human_readable(stage['startTs'])
            end_time = convert_to_human_readable(stage['endTs'])
            if last_status.get(stage_key) != (start_time, end_time):
                changes.append(f"Stage: {stage['name']} - Status: {stage['status']} - Start Time: {start_time} - End Time: {end_time}")
                last_status[stage_key] = (start_time, end_time)

            if stage['failureMessage'] and last_status.get(f"{stage_key}_failure_message") != stage['failureMessage']:
                table = PrettyTable()
                table.field_names = ["Scope", "Message"]
                table.add_row(["Stage", stage['failureMessage']])
                changes.append(table.get_string())
                last_status[f"{stage_key}_failure_message"] = stage['failureMessage']

            if stage['status'] in ['Running', 'Success', 'Failed','AsyncWaiting', 'Paused']:
                step_details = get_step_details(plan_execution_id, stage['nodeExecutionId'])
                debug_print(f"Steps_Details: {step_details}")
                if step_details:
                    steps = []
                    for step_id, step_info in step_details.items():
                        if step_info['status'] in ['Running', 'Success', 'Failed', 'Errored', 'AsyncWaiting', 'Paused']:
                            failure_message = step_info.get('failureInfo', {})
                            steps.append({
                                'name': step_info['name'],
                                'status': step_info['status'],
                                'startTs': step_info.get('startTs', 0),
                                'endTs': step_info.get('endTs', 0),
                                'failureMessage': failure_message.get('message', '') if failure_message else ''
                            })

                    steps.sort(key=lambda x: x['startTs'])

                    for step in steps:
                        if step_info.get('stepType', '') == 'Background':
                            debug_print(f"Skipping Background step: {step['name']}")
                            continue
                        debug_print(f"Checking Step: {step['name']}")
                        step_key = f"{stage['name']}_{step['name']}_{step['status']}"
                        step_start_time = convert_to_human_readable(step['startTs'])
                        step_end_time = convert_to_human_readable(step['endTs'])
                        if last_status.get(step_key) != (step_start_time, step_end_time):
                            changes.append(f"  Step: {step['name']} - Status: {step['status']} - Start Time: {step_start_time} - End Time: {step_end_time}")
                            last_status[step_key] = (step_start_time, step_end_time)
                            debug_print(stage)
                            json_data = get_pipeline_execution_json(plan_execution_id, ACCOUNT_IDENTIFIER, ORG_IDENTIFIER, PROJECT_IDENTIFIER, ACCOUNT_IDENTIFIER, API_KEY, stage['nodePlanId'])
                            logs = get_logs_from_json(json_data, API_KEY, ACCOUNT_IDENTIFIER, stage['name'])
                            debug_print(f"Found logs {logs}")
                            for log_entry in logs:
                                debug_print(f"Log line: {log_entry}")
                                if log_entry['step'] == step['name']:
                                    changes.append("------------------------------------------------")
                                    changes.append(f"Stage: {log_entry['stage']} - Step: {log_entry['step']} - Timeout: {log_entry['timeout']}")

                                    if 'time' in log_entry:
                                        changes.append(f"{log_entry['time']} - {log_entry['out']}")
                                    elif 'log' in log_entry:
                                        try:
                                            log_lines = log_entry['log'].split('\n')
                                            for line in log_lines:
                                                if line.strip():  # Ignore empty lines
                                                    log_data = json.loads(line)
                                                    inner_time = log_data.get('time', '')
                                                    inner_msg = log_data.get('msg', '')
                                                    changes.append(f"{log_data['out']}")
                                                    if inner_time and inner_msg:
                                                        changes.append(f"{inner_time} - {inner_msg}")
                                        except json.JSONDecodeError as e:
                                            changes.append(f"Error parsing log entry: {e}")
                                    else:
                                        changes.append(f"{log_entry['out']}")

        if changes:
            print("\n".join(changes))
            print("------------------------------------------------")

        if status not in ['Running', 'Pending', 'AsyncWaiting', 'Paused']:
            completed = True

        time.sleep(10)

    if status in ['Failed', 'Errored']:
        print("Pipeline execution failed.")
        exit(2)

if __name__ == "__main__":
    print_header()
    pipeline_response = trigger_pipeline()
    if 'data' in pipeline_response and 'planExecution' in pipeline_response['data']:
        plan_execution_id = pipeline_response['data']['planExecution']['uuid']
        monitor_pipeline(plan_execution_id, debug=False)
    else:
        print("Failed to trigger pipeline:", pipeline_response)
        exit(2)
