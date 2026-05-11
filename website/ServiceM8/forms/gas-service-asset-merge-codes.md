# Gas Service & Maintenance — Asset: Field → Merge-Code Map

All 83 active fields with their **ServiceM8 Template Field Code** — the string you drop into the Word `«MergeField»`.

> SM8 auto-generates the codes from each field's name using a fixed rule: `form_<lowercase_slug>` for text-type fields (Text, Multi-Line, Number, Date, Multiple Choice) and `image_form_<lowercase_slug>` for image-type fields (Photo, Signature). The codes below match the real values shown in the SM8 form editor — note that they are not exposed via the public API, so this table is the canonical reference for use in the Word template.

Use directly in Word: `«form_appliance_type»`, `«image_form_engineer_signature»`, etc. Insert via **Insert → Quick Parts → Field → MergeField** and type the code as the Field name.

| # | Field name | Type | M | Template Field Code |
|---|---|---|---|---|
| 1 | Appliance Type | Multiple Choice | ✓ | `form_appliance_type` |
| 2 | Visual Inspection | Multiple Choice | ✓ | `form_visual_inspection` |
| 3 | Boiler Pressure Photo Before | Photo |  | `image_form_boiler_pressure_photo_before` |
| 4 | Stability | Multiple Choice | ✓ | `form_stability` |
| 5 | Location | Multiple Choice | ✓ | `form_location` |
| 6 | Ventilation | Multiple Choice | ✓ | `form_ventilation` |
| 7 | Leaks | Multiple Choice | ✓ | `form_leaks` |
| 8 | Pipework | Multiple Choice | ✓ | `form_pipework` |
| 9 | Case & Combustion Seals | Multiple Choice | ✓ | `form_case_combustion_seals` |
| 10 | Electrics | Multiple Choice | ✓ | `form_electrics` |
| 11 | Inside Boiler Photo | Photo | ✓ | `image_form_inside_boiler_photo` |
| 12 | Flue Gas | Multiple Choice | ✓ | `form_flue_gas` |
| 13 | Flue Gas Initial Final | Multiple Choice | ✓ | `form_flue_gas_initial_final` |
| 14 | Flue Gas Initial Photo | Photo | ✓ | `image_form_flue_gas_initial_photo` |
| 15 | Flue Gas Ratio Initial | Text | ✓ | `form_flue_gas_ratio_initial` |
| 16 | Flue Gas PPM Initial | Text | ✓ | `form_flue_gas_ppm_initial` |
| 17 | Flue Gas Percentage Initial | Text | ✓ | `form_flue_gas_percentage_initial` |
| 18 | Burner | Multiple Choice | ✓ | `form_burner` |
| 19 | Heat Exchanger | Multiple Choice | ✓ | `form_heat_exchanger` |
| 20 | Ignition | Multiple Choice | ✓ | `form_ignition` |
| 21 | Controls | Multiple Choice | ✓ | `form_controls` |
| 22 | Fan | Multiple Choice | ✓ | `form_fan` |
| 23 | Fireplace | Multiple Choice | ✓ | `form_fireplace` |
| 24 | Closure Plate | Multiple Choice | ✓ | `form_closure_plate` |
| 25 | Flame | Multiple Choice | ✓ | `form_flame` |
| 26 | Flue Flow | Multiple Choice | ✓ | `form_flue_flow` |
| 27 | Flue Termination | Multiple Choice | ✓ | `form_flue_termination` |
| 28 | Spillage | Multiple Choice | ✓ | `form_spillage` |
| 29 | Condensate | Multiple Choice | ✓ | `form_condensate` |
| 30 | Safety Devices | Multiple Choice | ✓ | `form_safety_devices` |
| 31 | Return Air | Multiple Choice | ✓ | `form_return_air` |
| 32 | Tightness Test | Multiple Choice | ✓ | `form_tightness_test` |
| 33 | Tightness Value | Text | ✓ | `form_tightness_value` |
| 34 | Standing Pressure Photo | Photo | ✓ | `image_form_standing_pressure_photo` |
| 35 | Standing Pressure | Text |  | `form_standing_pressure` |
| 36 | Working Pressure | Multiple Choice | ✓ | `form_working_pressure` |
| 37 | Working Pressure Meter Appliance | Multiple Choice | ✓ | `form_working_pressure_meter_appliance` |
| 38 | Working Pressure Meter Photo | Photo | ✓ | `image_form_working_pressure_meter_photo` |
| 39 | Working Pressure Meter | Text | ✓ | `form_working_pressure_meter` |
| 40 | Gas Rate | Multiple Choice | ✓ | `form_gas_rate` |
| 41 | Gas Rate Value | Text | ✓ | `form_gas_rate_value` |
| 42 | Gas Rate Result | Multiple Choice | ✓ | `form_gas_rate_result` |
| 43 | Gas Rate Photo | Photo | ✓ | `image_form_gas_rate_photo` |
| 44 | Working Pressure Appliance Photo | Photo | ✓ | `image_form_working_pressure_appliance_photo` |
| 45 | Working Pressure Appliance | Text | ✓ | `form_working_pressure_appliance` |
| 46 | Working Pressure Result | Multiple Choice | ✓ | `form_working_pressure_result` |
| 47 | Burner Pressure | Multiple Choice | ✓ | `form_burner_pressure` |
| 48 | Burner Pressure Photo | Photo | ✓ | `image_form_burner_pressure_photo` |
| 49 | Burner Pressure Value | Text | ✓ | `form_burner_pressure_value` |
| 50 | Burner Pressure Result | Multiple Choice | ✓ | `form_burner_pressure_result` |
| 51 | Flue Integrity Photo | Photo |  | `image_form_flue_integrity_photo` |
| 52 | Flue Integrity | Multiple Choice |  | `form_flue_integrity` |
| 53 | Flue Gas Final Photo Max | Photo | ✓ | `image_form_flue_gas_final_photo_max` |
| 54 | Flue Gas Ratio Final Max | Text | ✓ | `form_flue_gas_ratio_final_max` |
| 55 | Flue Gas PPM Final Max | Text | ✓ | `form_flue_gas_ppm_final_max` |
| 56 | Flue Gas Percentage Max | Text | ✓ | `form_flue_gas_percentage_max` |
| 57 | Flue Gas Final Photo Min | Photo |  | `image_form_flue_gas_final_photo_min` |
| 58 | Flue Gas Ratio Final Min | Text |  | `form_flue_gas_ratio_final_min` |
| 59 | Flue Gas PPM Final Min | Text |  | `form_flue_gas_ppm_final_min` |
| 60 | Flue Gas Percentage Min | Text |  | `form_flue_gas_percentage_min` |
| 61 | Flue Gas Result | Multiple Choice | ✓ | `form_flue_gas_result` |
| 62 | Expansion Vessel | Multiple Choice | ✓ | `form_expansion_vessel` |
| 63 | System Filter | Multiple Choice | ✓ | `form_system_filter` |
| 64 | System Photo | Multiple Choice | ✓ | `form_system_photo` |
| 65 | System Filter Photo Before | Photo | ✓ | `image_form_system_filter_photo_before` |
| 66 | System Filter Photo After | Photo | ✓ | `image_form_system_filter_photo_after` |
| 67 | Service Type | Multiple Choice | ✓ | `form_service_type` |
| 68 | Manufacturer | Multiple Choice | ✓ | `form_manufacturer` |
| 69 | Boiler Pressure Photo After | Photo |  | `image_form_boiler_pressure_photo_after` |
| 70 | Water Quality Test | Multiple Choice | ✓ | `form_water_quality_test` |
| 71 | Water Qualty Test Results | Multiple Choice | ✓ | `form_water_qualty_test_results` |
| 72 | Additional Photo 1 | Photo |  | `image_form_additional_photo_1` |
| 73 | Additional Photo 2 | Photo |  | `image_form_additional_photo_2` |
| 74 | Additional Photo 3 | Photo |  | `image_form_additional_photo_3` |
| 75 | Additional Photo 4 | Photo |  | `image_form_additional_photo_4` |
| 76 | Additional Photo 5 | Photo |  | `image_form_additional_photo_5` |
| 77 | Safe To Use | Multiple Choice | ✓ | `form_safe_to_use` |
| 78 | Warning Notice | Multiple Choice | ✓ | `form_warning_notice` |
| 79 | Engineer Notes | Text (Multi-Line) |  | `form_engineer_notes` |
| 80 | Engineer Signature | Signature | ✓ | `image_form_engineer_signature` |
| 81 | Customer Name | Text |  | `form_customer_name` |
| 82 | Customer Signature | Signature |  | `image_form_customer_signature` |
| 83 | Recommendations | Multiple Choice (Multi-Answer) |  | `form_recommendations` |

## Special / built-in merge fields

Beyond your form's own fields, SM8 exposes built-ins you can drop into the same template (these don't depend on the form):

- `recipient_first` — customer's first name
- `job.job_address` — full site address
- `job.generated_job_id` — public job/invoice number
- `job.category` — job category label
- `job.completion_date` — when the job was completed
- `job.contact_first` / `job.contact_last` — primary site contact
- `vendor.name` — "Better Call Wes"
- `vendor.email` / `vendor.website` / `location.phone_1`
- `image_company_logo` — your business logo
- `image_customer_signature` / `image_form_signed` — special image merge fields
- `calculation.current_user_fullname` — engineer doing the form

These are the same tokens used in your existing email templates (see `~/obsidian-vault/Better-Call-Wes/ServiceM8-Email-Templates.md`).