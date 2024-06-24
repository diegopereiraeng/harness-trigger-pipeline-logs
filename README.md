# harness-trigger-pipeline-logs

## Usage Example

```yaml
- step:
    type: Plugin
    name: Trigger Pipeline
    identifier: Trigger_Pipeline
    spec:
      connectorRef: account.DockerHubDiego
      image: diegokoala/harness-trigger-pipeline-logs:<+pipeline.stages.plugin_image_builder.spec.execution.steps.BuildAndPushDockerRegistry.artifact_BuildAndPushDockerRegistry.stepArtifacts.publishedImageArtifacts[0].tag>
      settings:
        API_KEY: <+secrets.getValue("diego_pat")>
        ACCOUNT_IDENTIFIER: <account_id>
        ORG_IDENTIFIER: SE_Sandbox
        PROJECT_IDENTIFIER: Platform_Engineering
        PIPELINE_IDENTIFIER: financebackenddeploy
        PIPELINE_YAML: "pipeline:\\n  identifier: financebackenddeploy\\n  properties:\\n    ci:\\n      codebase:\\n        build:\\n          spec:\\n            branch: main\\n          type: branch"
        DEBUG: "true"
```
