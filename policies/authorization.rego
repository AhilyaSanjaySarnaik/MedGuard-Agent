package medguard.authz

default allow = false

# Allow access to patient records if user is an assigned doctor
allow {
    input.agent.role == "clinical_assistant"
    input.request.tool_name == "get_patient_record"
    user_is_assigned_doctor
}

user_is_assigned_doctor {
    input.user.role == "doctor"
    input.user.user_id == input.patient.assigned_doctor_id
}

# Allow lab results query for active care team members
allow {
    input.agent.role == "clinical_assistant"
    input.request.tool_name == "get_lab_results"
    input.user.role == "doctor"
}