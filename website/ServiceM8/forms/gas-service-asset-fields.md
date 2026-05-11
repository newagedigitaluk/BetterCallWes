# Gas Service and Maintenance Record — Asset

Field reference for designing the company document template generated from this form.

## Form metadata

- Form UUID: `38ee6e7d-a2b1-476d-a50a-e863be3b8316`
- Document template UUID (existing, to restyle): `2a5fbbf8-6d1e-4af3-8afb-1dfac48bff7b`
- Badge: `Service` (mandatory_state = `0`)
- Can be used independently: `0` (0 = only attached to a job)
- Last edited: 2026-04-29 16:30:26
- Active fields: **83**

## How conditional logic works in this form

Fields can be hidden/shown based on prior answers. Conditions reference the **UUID** of the controlling field (not its name). Operators seen on this form: `CON` (contains), `NCON` (does not contain), `EQ` (equals). When a condition is not met, the field has no answer — your document template needs to handle absent values gracefully (skip the row, or show `—`).

> **Sanity-check note:** several Yes/No questions show their follow-up fields when the answer is `No`. That is what's currently in the form data — worth eyeballing during template testing in case any conditions are inverted from intent.

## §Setup

#### 1. Appliance Type

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `4d0a69da-5aa6-4529-a00d-4f4d89b2ba70`
- Hint: What type of appliance is being worked on
- Choices:
  - Boiler
  - Fire
  - Range Cooker
  - Water Heater
  - Cooker
  - Hob
  - Oven
  - Warm Air Unit

## §Visual Inspection

#### 2. Visual Inspection

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `15690813-5cc0-4b9d-95bb-9067782b7b88`
- Hint:
  - Check the following
  - 1. Signs of damage
  - 2. Signs of poor installation
  - 3. Suitability of appliance
  - 4. Access for maintenance and servicing
  - 5. Proximity to combustible materials
  - 6. Presence of suitability and condition of any air	supply vents
  - 7. Condition suitability and sighting of any flue or	chimney	system
  - 8. Signs of overheating/distress
- Choices:
  - Visual Inspection is good
  - Visual Inspection has failed.

#### 3. Boiler Pressure Photo Before

- Type: `Photo` — optional
- Field UUID: `f797451d-523c-4808-956e-80e819ce3042`
- Hint: Photo of Boiler pressure before service

#### 4. Stability

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `9b873272-3968-4ddd-993d-f9791586662b`
- Hint: Is the appliance stable and fixed correctly?
- Choices:
  - The appliance is fixed secure and has good stabilty
  - The appliance is not fixed securely and has poor stability

#### 5. Location

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `5da6d15c-e17c-4d98-a212-646c82c0f5d6`
- Hint: Is the appliance's location acceptable?
- Choices:
  - The appliance is located in a suitable location
  - The Location is not suitable for this type of appliance

#### 6. Ventilation

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `f51af134-69e5-46a7-ba5f-bb49eeb96314`
- Hint: Is the ventilation correct for the appliance?
- Choices:
  - The appliance has the required amount of ventilation
  - The ventilation provision for this appliance is in adequate and needs attention

#### 7. Leaks

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `ef98186b-8ced-4a90-a858-92a6afafb67d`
- Hint: Condition of gas/water connections? Any leaks?
- Choices:
  - There are no gas/water visible leaks
  - There is evidence of a water leak but no leak currently present
  - There is a visible water leak which will require further attention
  - There is signs of a gas leak, which will require immediate attention

#### 8. Pipework

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `8717d096-0f5b-4c58-acc7-25bab43249b5`
- Hint: Does all gas pipework meet regulations?
- Choices:
  - Gas pipework meets current regulations
  - Gas pipework does not meet current regulations and needs attention

#### 9. Case & Combustion Seals

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `ed70b1ab-5eef-466c-be18-c8241284286f`
- Hint: Is the condition of the case and combustion seals acceptable
- Choices:
  - N/A
  - The case seals are intact and in good condition
  - The case seals are showing signs of distress and need attention
  - The seals are damaged and will need immediate attention

#### 10. Electrics

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `769fc81c-7220-4450-a9b7-ff01dd5e9760`
- Hint: Condition of appliance electrics?
- Choices:
  - N/A
  - Electrics are in good condition
  - Electrics are in poor condition and requires attention
  - Electrics are unsafe and requires immediate attention

## §Internal Inspection

#### 11. Inside Boiler Photo

- Type: `Photo` — **MANDATORY**
- Field UUID: `915a6836-7687-4818-913b-073efe613cb5`
- Hint: Photo of inside of boiler
- Show if: `Appliance Type` NCON "Boiler"

## §Initial Flue Gas Analysis

#### 12. Flue Gas

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `76ee65f4-5878-4a12-a4db-290223c197c3`
- Hint: Has a flue gas analysis been performed?
- Choices:
  - Yes
  - No

#### 13. Flue Gas Initial Final

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `e5996d27-7f77-4423-89a2-3614de9bd320`
- Hint: Was the analysis performed before AND after the service or only after?
- Choices:
  - After
  - Both
- Show if: `Flue Gas` CON "No"

#### 14. Flue Gas Initial Photo

- Type: `Photo` — **MANDATORY**
- Field UUID: `3938c355-3022-46aa-b5ad-1f02aa3f75cf`
- Hint: Take a photo of the initial flue gas analyser reading
- Show if: `Flue Gas` CON "No" **OR** `Flue Gas Initial Final` CON "After"

#### 15. Flue Gas Ratio Initial

- Type: `Text` — **MANDATORY**
- Field UUID: `6db4c128-f3c6-4edf-a62d-e5e6e65909bb`
- Hint: Please enter the initial CO/CO2 ratio readings.
- Show if: `Flue Gas` CON "No" **OR** `Flue Gas Initial Final` CON "After"

#### 16. Flue Gas PPM Initial

- Type: `Text` — **MANDATORY**
- Field UUID: `209825bd-ebb7-4292-bcec-3f69717cb417`
- Hint: Please enter the initial CO ppm.
- Show if: `Flue Gas` CON "No" **OR** `Flue Gas Initial Final` CON "After"

#### 17. Flue Gas Percentage Initial

- Type: `Text` — **MANDATORY**
- Field UUID: `83e73496-eaf7-4303-ab14-709611250b2e`
- Hint: Please enter the Initial CO2 percentage reading.
- Show if: `Flue Gas` CON "No" **OR** `Flue Gas Initial Final` CON "After"

## §Combustion & Components

#### 18. Burner

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `32585cfa-36d1-451e-bea4-0207125ab210`
- Hint: Condition of burners/injectors?
- Choices:
  - N/A
  - Cleaned burner and injectors
  - Burner Injectors showing signs of distress, require attention

#### 19. Heat Exchanger

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `297c07ae-27d5-47a2-b15a-5ac7ea30ee6e`
- Hint: Condition of the heat exchanger?
- Choices:
  - N/A
  - Cleaned Heat Exchanger
  - Passed combustion checks & visual inspection good
  - Heat exchanger showing signs of distress
  - Heat exchanger showing signs of water damage
  - Heat exchanger in need of immediate attention
- Show if: `Appliance Type` CON "Fire" **AND** `Appliance Type` CON "Cooker" **AND** `Appliance Type` CON "Hob"

#### 20. Ignition

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `ddb8212d-fae0-49cf-b1df-ea2272742cba`
- Hint: Do the ignition components operate correctly?
- Choices:
  - N/A
  - Ignition is good
  - Ignition is good, electrodes cleaned 
  - Ignition is poor and requires attention
  - Ignition is explosive and require attention

#### 21. Controls

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `1cd992cc-97af-4338-a421-b288ece92a36`
- Hint: Do the appliance controls operate correctly?
- Choices:
  - N/A
  - The appliance controls are operating normally
  - The appliance controls appear not to be functioning correctly and require attention

#### 22. Fan

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `cfa0016a-6bfc-42a2-8569-30be84986694`
- Hint: Does the fan/air pressure switch operate correctly?
- Choices:
  - N/A
  - Fan runs smoothly
  - Fan runs but is a little noisy
  - Fan runs but is very noisy, requires attention

#### 23. Fireplace

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `3eaaf173-80c7-4c4e-bbbf-91bcbc4f6584`
- Hint: Is the fireplace opening/void correct?
- Choices:
  - The fireplace opening is good
  - The fireplace opening is incorrect and requires attention
- Show if: `Appliance Type` NCON "Fire"

#### 24. Closure Plate

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `30d68608-f26c-440c-86f1-bd702cae4c9d`
- Hint: Is the closure plate installed correctly?
- Choices:
  - N/A
  - Closure plate is fitted correctly and sealed with closure plate tape
  - Closure plate is not correct and requires attention 
- Show if: `Appliance Type` NCON "Fire"

#### 25. Flame

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `7f548730-bfb4-4ef7-bf0c-6410f4a91721`
- Hint: Is the flame picture acceptable?
- Choices:
  - N/A
  - The flame picture is good
  - The flame picture is poor

#### 26. Flue Flow

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `3bdcb32a-9518-44d8-ab1f-9010362b6f70`
- Hint: Flue flow test result.
- Choices:
  - N/A
  - The chimney/flue has a good pull
  - The chimney/flue is not pulling sufficiently
  - The chimney/flue is leaking products of combustion

#### 27. Flue Termination

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `16c6bdac-1586-462f-8454-c5a0af1ab24e`
- Hint: Is the flue terminal/termination correct?
- Choices:
  - N/A
  - Flue termination is good
  - Flue termination has an issue needs attention

#### 28. Spillage

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `f3b3d37c-c566-4345-9f93-8d46ab2ea170`
- Hint: Spillage test result.
- Choices:
  - N/A
  - The appliance is not spilling any products of combustion
  - The appliance is spilling products of combustion and needs immediate attention

#### 29. Condensate

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `dfaf8620-3e61-4a2e-849f-e0dce1e96b93`
- Hint: Does the condensate pipework terminate correctly? Is the condensate trap clean and sealed correctly?
- Choices:
  - N/A
  - The condensate trap has been cleaned and terminates correctly
  - The condensate trap has been cleaned but is not fitted to regulations

#### 30. Safety Devices

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `a4103611-19ef-4266-93d4-03f97b14d4cb`
- Hint: Are the safety devices operating correctly?
- Choices:
  - N/A
  - Safety devices are operating correctly
  - Safety devices have failed to operate correctly

#### 31. Return Air

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `54026a05-633e-451a-a801-a92ace439878`
- Hint: Is the return air/plenum correct?
- Choices:
  - N/A
  - The plenum is operating correctly
  - The plenum is operating incorrectly
- Show if: `Appliance Type` NCON "Warm Air Unit"

## §Gas Tightness & Pressure

#### 32. Tightness Test

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `8b13b03c-640a-49fb-978b-4540ecd4879f`
- Hint: Did the installation pass or fail the tightness test?
- Choices:
  - The tightness test has passed and there is no escape of gas
  - The tightness test has passed although there is a slight escape but within the limits
  - The tightness test has failed as there is a leak in the gas pipework

#### 33. Tightness Value

- Type: `Text` — **MANDATORY**
- Field UUID: `c9958fc5-4cad-4f31-9e6d-1972285262d5`
- Hint: Please enter pressure gain or loss.

#### 34. Standing Pressure Photo

- Type: `Photo` — **MANDATORY**
- Field UUID: `7f4538c7-da68-4990-a7ca-2eac76a791c6`

#### 35. Standing Pressure

- Type: `Text` — optional
- Field UUID: `4be41e85-8b37-4619-a1ce-3820f190029a`

#### 36. Working Pressure

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `94ff1641-53f2-4f00-8150-ac81175e02ed`
- Hint: Has the working pressure been checked at the meter or appliance?
- Choices:
  - Yes
  - No

#### 37. Working Pressure Meter Appliance

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `5d88736f-6b60-4852-8dac-d98b0d008df8`
- Hint: Was the working pressure measured at the meter, appliance or both?
- Choices:
  - Meter
  - Appliance
  - Both
- Show if: `Working Pressure` CON "No"

#### 38. Working Pressure Meter Photo

- Type: `Photo` — **MANDATORY**
- Field UUID: `0f053fde-fd0b-4d05-90d1-7b7fb15c253e`
- Hint: Take picture of working pressure reading at meter
- Show if: `Working Pressure` CON "No" **OR** `Working Pressure Meter Appliance` CON "Appliance"

#### 39. Working Pressure Meter

- Type: `Text` — **MANDATORY**
- Field UUID: `4a8355eb-6daf-4f55-a414-0bef68b51a73`
- Hint: Please provide the gas meter working pressure.
- Show if: `Working Pressure` CON "No" **OR** `Working Pressure Meter Appliance` CON "Appliance"

#### 40. Gas Rate

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `e46437ef-dba5-4527-a3cb-58401dc30fb2`
- Hint: Has a gas rate been taken?
- Choices:
  - Yes
  - No

#### 41. Gas Rate Value

- Type: `Text` — **MANDATORY**
- Field UUID: `b4becba5-88b9-4b18-8dd7-d8c90f57ce56`
- Hint: Please enter the gas rate result in KW.
- Show if: `Gas Rate` CON "No"

#### 42. Gas Rate Result

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `4d9f1a1d-640d-4fbb-8acb-ded46bede1a6`
- Hint: Was the gas rate recorded acceptable?
- Choices:
  - The gas rate is good and within acceptable values
  - The gas rate has failed and values unacceptable
- Show if: `Gas Rate` CON "No"

#### 43. Gas Rate Photo

- Type: `Photo` — **MANDATORY**
- Field UUID: `c91f2b4c-10ba-4e75-b9c9-d0084601d205`
- Hint: Please include photo of gas rate result
- Show if: `Gas Rate` CON "No"

#### 44. Working Pressure Appliance Photo

- Type: `Photo` — **MANDATORY**
- Field UUID: `f75d4f3b-5bf6-4cbc-8724-b61facd9bdd7`
- Hint: Take picture of working pressure reading at appliance
- Show if: `Working Pressure` CON "No"

#### 45. Working Pressure Appliance

- Type: `Text` — **MANDATORY**
- Field UUID: `1cb9d4bc-70b4-40e0-946e-0aef6ddbffe8`
- Hint: Please provide the working pressure at the appliance.
- Show if: `Working Pressure` CON "No" **OR** `Working Pressure Meter Appliance` CON "Meter"

#### 46. Working Pressure Result

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `53afcc80-1bf3-4672-82e7-4b88da77c2c4`
- Hint: Were the working pressures measured acceptable?
- Choices:
  - The working pressure measured is good
  - The working pressure measured is below the acceptable value, requires investigation
- Show if: `Working Pressure` CON "No"

#### 47. Burner Pressure

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `2fac3514-931b-4bad-a221-697ccac3a56d`
- Hint: Has the burner pressure been taken?
- Choices:
  - No
  - Yes

#### 48. Burner Pressure Photo

- Type: `Photo` — **MANDATORY**
- Field UUID: `c25faee6-5181-42a2-aac7-c47ce0a093cc`
- Hint: Take picture of burner pressure reading
- Show if: `Burner Pressure` CON "No"

#### 49. Burner Pressure Value

- Type: `Text` — **MANDATORY**
- Field UUID: `fc30d64c-424c-4916-bff6-10414a4d476b`
- Hint: Please enter the burner pressure in mbar.
- Show if: `Burner Pressure` CON "No"

#### 50. Burner Pressure Result

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `cb7f868c-ffac-4a2f-bbb5-746f4d032320`
- Hint: Is the burner pressure correct/acceptable?
- Choices:
  - The burner pressure is correct
  - The burner pressure is within the acceptable tolorances
  - The burner is out of the required tolerances and requires attention
- Show if: `Burner Pressure` CON "No"

## §Final Flue Gas Analysis

#### 51. Flue Integrity Photo

- Type: `Photo` — optional
- Field UUID: `040ae9fc-5ff8-41ae-be15-29ba573c17dc`
- Hint: Photo of flue integrity result
- Show if: `Flue Gas` CON "No"

#### 52. Flue Integrity

- Type: `Multiple Choice` — optional
- Field UUID: `3c95315c-7458-4910-b5cb-d2f0514cb213`
- Hint: What are the results of the flue integrity test
- Choices:
  - N/A
  - Flue integrity is good no leaks of co into air intake
  - Flue Integrity has failed, will need immediate attention
- Show if: `Flue Gas` EQ "No"

#### 53. Flue Gas Final Photo Max

- Type: `Photo` — **MANDATORY**
- Field UUID: `be662553-a737-4eb7-ac06-b24c1c2394c3`
- Hint: Take picture of working flue gas final reading at full load.
- Show if: `Flue Gas` CON "No"

#### 54. Flue Gas Ratio Final Max

- Type: `Text` — **MANDATORY**
- Field UUID: `8bfc4ea5-ffab-4c3c-8bfb-ed6d48745e80`
- Hint: Please enter the final CO/CO2 ratio at full load.
- Show if: `Flue Gas` CON "No"

#### 55. Flue Gas PPM Final Max

- Type: `Text` — **MANDATORY**
- Field UUID: `0685d080-890f-4508-82d1-1a472e796177`
- Hint: Please enter the final CO ppm reading at full load.
- Show if: `Flue Gas` CON "No"

#### 56. Flue Gas Percentage Max

- Type: `Text` — **MANDATORY**
- Field UUID: `9fb92c2e-1a93-4899-85bb-046040fa32ab`
- Hint: Please enter the final CO2 percentage reading full load.
- Show if: `Flue Gas` CON "No"

#### 57. Flue Gas Final Photo Min

- Type: `Photo` — optional
- Field UUID: `326683ee-5375-4136-bfe2-fff8e44cf523`
- Hint: Take picture of working flue gas final reading at part load.
- Show if: `Flue Gas` CON "No"

#### 58. Flue Gas Ratio Final Min

- Type: `Text` — optional
- Field UUID: `dfc241ef-adfc-469e-be75-da14a123348c`
- Hint: Please enter the final CO/CO2 ratio at part load.
- Show if: `Flue Gas` CON "No"

#### 59. Flue Gas PPM Final Min

- Type: `Text` — optional
- Field UUID: `9dc8ac87-c986-4425-a18a-0f80da6dc984`
- Hint: Please enter the final CO ppm reading at part load.
- Show if: `Flue Gas` CON "No"

#### 60. Flue Gas Percentage Min

- Type: `Text` — optional
- Field UUID: `1314675b-8fe1-407b-96a2-74931079cec4`
- Hint: Please enter the final CO2 percentage reading part load.
- Show if: `Flue Gas` CON "No"

#### 61. Flue Gas Result

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `7aacb5d3-302d-470e-b9bc-4c8fff9d6a1a`
- Hint: Was the outcome of the flue gas analysis acceptable?
- Choices:
  - The flue analysis was good and readings acceptable
  - The flue analysis was bad and readings unacceptable, needs further investigation
- Show if: `Flue Gas` CON "No"

## §System Components

#### 62. Expansion Vessel

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `114f7fe0-ae60-434f-9e94-97201fac2461`
- Hint: Check expansion vessel has the correct charge.
- Choices:
  - N/A
  - Expansion vessel has been recharged 
  - Expansion vessel has split and will need to be replaced
  - Expansion vessel is at required charge
  - Expansion vessel tube is blocked

#### 63. System Filter

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `f586aaf1-2efa-41c2-8369-ab8f804d54cb`
- Hint: Has the system filter been checked and cleaned
- Choices:
  - N/A
  - Has been checked and cleaned
  - There is no filter installed

#### 64. System Photo

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `81195d98-2a24-4fe7-ba59-cc018a3ba4c7`
- Hint: Can photos be taken of the filter
- Choices:
  - No
  - Before & After
  - No Just After
- Show if: `System Filter` EQ "N/A" **OR** `System Filter` CON "no"

#### 65. System Filter Photo Before

- Type: `Photo` — **MANDATORY**
- Field UUID: `0c5fa012-5ef0-4f6f-a24b-bd06eeb7fc95`
- Hint: Photo of system filter before cleaning
- Show if: `System Filter` CON "N/A" **OR** `System Photo` CON "Just" **OR** `System Filter` CON "no"

#### 66. System Filter Photo After

- Type: `Photo` — **MANDATORY**
- Field UUID: `1205804b-5e4f-42c7-9b44-8506c3f96598`
- Hint: Photo of system filter after cleaning
- Show if: `System Filter` CON "no" **OR** `System Filter` EQ "N/A" **OR** `System Photo` CON "no"

## §Service Wrap-up

#### 67. Service Type

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `0d6e2c4d-6fdd-4791-8504-0350c0a14fc8`
- Hint: Was the service a full strip down service?
- Choices:
  - A standard boiler service has been completed
  - A full strip down boiler service has been completed

#### 68. Manufacturer

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `7762564d-5e17-4a19-84e5-a4621afb7653`
- Hint: Does the installation meet the manufacturer's instructions?
- Choices:
  - Yes
  - No

#### 69. Boiler Pressure Photo After

- Type: `Photo` — optional
- Field UUID: `03e93c37-4ff0-4239-b0f3-8083decaa1d6`
- Hint: Photo of Boiler pressure after service

#### 70. Water Quality Test

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `3bf449ad-d45c-4713-a9c2-146664c944e5`
- Hint: Has a water quality check of the heating system been done?
- Choices:
  - Yes
  - No

#### 71. Water Qualty Test Results

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `23c1f559-a53e-45f3-903e-c5d4da7ff490`
- Hint: What were the results of the water test.
- Choices:
  - Inhibitor, Corrosion & pH level all passed. Water quality good
  - Inhibitor & Corrosion levels passed, pH level failed. Needs attention
  - Inhibitor & pH levels passed, Corrosion level failed. Needs attention
  - Corrosion & pH levels passed, Inhibitor level failed. Needs attention
  - Inhibitor level passed, Corrosion & pH levels failed. Needs attention
  - Corrosion level passed, Inhibitor & pH levels failed. Needs attention
  - pH level passed, Corrosion & Inhibitor levels failed. Needs attention
  - Inhibitor, Corrosion & pH level all failed. Water quality poor
- Show if: `Water Quality Test` CON "No"

## §Additional Photos

#### 72. Additional Photo 1

- Type: `Photo` — optional
- Field UUID: `7309b60e-f1a6-4faf-a6af-68729b07389a`
- Hint: Photos of any relevent information

#### 73. Additional Photo 2

- Type: `Photo` — optional
- Field UUID: `071eb9e3-80bb-4e13-b325-6b04ca665c5b`
- Hint: Photos of any relevant information

#### 74. Additional Photo 3

- Type: `Photo` — optional
- Field UUID: `0afd3aaf-4ba3-4ec8-b562-25bc14139e92`
- Hint: Photos of any relevant information

#### 75. Additional Photo 4

- Type: `Photo` — optional
- Field UUID: `8ce3d3f8-c628-42e2-8a9b-df8572fe524a`
- Hint: Photos of any relevant information

#### 76. Additional Photo 5

- Type: `Photo` — optional
- Field UUID: `86470468-4ec5-4b2e-8fa6-ff810c14522f`
- Hint: Photos of any relevant information

## §Safety Outcomes

#### 77. Safe To Use

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `c8a32f62-344c-4de4-bffd-a938d5e4f6e8`
- Hint: Is the appliance/installation safe to use?
- Choices:
  - Yes
  - No - Please see additional information

#### 78. Warning Notice

- Type: `Multiple Choice` — **MANDATORY**
- Field UUID: `7f0d58fc-7127-45fb-8ebb-6d56d84db2c6`
- Hint: Has a warning notice been issued?
- Choices:
  - Yes
  - No

## §Sign-off

#### 79. Engineer Notes

- Type: `Text (Multi-Line)` — optional
- Field UUID: `e8522bad-483b-44a2-89a7-4cf5a805e738`
- Hint: Please enter any notes/remedial action required. This field is not required.

#### 80. Engineer Signature

- Type: `Signature` — **MANDATORY**
- Field UUID: `f5c057ae-8ba5-479d-ab76-3cfef43183dc`
- Hint: Please provide the Gas Safe Engineers signature.

#### 81. Customer Name

- Type: `Text` — optional
- Field UUID: `fcb270a6-41bf-4af9-b32e-598aacb323d7`
- Hint: Please enter the responsible person's name.

#### 82. Customer Signature

- Type: `Signature` — optional
- Field UUID: `1e29d2a4-ef51-4be8-9150-917d3d2266f3`
- Hint: Please sign to accept this service certificate.

## §Recommendations

#### 83. Recommendations

- Type: `Multiple Choice (Multi-Answer)` — optional
- Field UUID: `e2bd9ff8-2b07-4187-8782-a9adc0fab652`
- Hint: Are there any Recommendations you would advise
- Choices:
  - New Boiler
  - Powerflush
  - Magnetic Filter
  - Smart Thermostat
