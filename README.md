# EC528-Fall-2025-CloudNeuro-Tekton

## To the Cloud: Neuroscience Pipelines on Tekton

### Problem Statement
While neuroimaging research produces software tools with the potential to improve clinical outcomes and reduce physicians’ workload, the inefficiencies in usability and integration hinders the realization of this potential. Existing proprietary automation and AI platforms and prohibitively expensive, often requiring not only steep licensing feeds but also in-house developers to customize them. Even when available, such tools impose steep learning curves and disrupt established clinical routines, leaving busy clinicians unable to adopt them. Usability and seamless integration are therefore essential prerequisites for translating research advances into practice.

### 1. Vision and Goals Of The Project
Our minimum goal is to demonstrate the execution of neuroimaging research software, such as FreeSurfer, on OpenShift using Tekton/OpenShift pipelines. This involves packaging existing neuroimaging tools so they can run efficiently and reliably in a cloud-native environment, thereby automating pipeline execution and facilitating computational reproducibility through consistent containerized environments.

Beyond this baseline, the project aims to address the broader challenges identified in clinical adoption by emphasizing three guiding principles:

* Usability and Clinical Accessibility (Branch A) – Automation in the cloud is only the first step. For clinicians to benefit, tools must be intuitive, low-friction, and aligned with existing workflows. Branch A focuses on building a user-facing platform for triggering pipeline execution, monitoring progress, and visualizing outputs. This layer transforms containerized pipelines into a usable clinical tool, addressing the steep learning curves and workflow disruptions that currently prevent adoption.
* Scalability and Infrastructure Interoperability (Branch B) – Cloud computing provides elastic, pay-as-you-go compute capacity that is especially valuable for institutions without dedicated HPC infrastructure, lowering the barrier for smaller or resource-limited hospitals to run advanced neuroimaging pipelines. At the same time, institutions with existing HPC systems may see less value in cloud elasticity. For these cases, interoperability becomes crucial. Branch B explores translating Tekton pipelines into formats such as SLURM or Argo, ensuring that pipelines can run across diverse infrastructures and integrate with existing systems.
* Transparency and Trust – Existing proprietary platforms impose steep licensing fees for products that often remain opaque and require further customization. By building on open-source software and cloud-native standards such as Tekton, we enable transparency, interoperability, and community-driven trust, ensuring the software can be inspected, extended, and widely adopted.

### 2. Users/Personas Of The Project
Neuroimaging research is both computationally intensive and requires advanced technical knowledge of the Linux command-line. Cloud-native tools such as Kubernetes and Tekton provide opportunities for elastic compute and integration with clinical systems. The personas differ depending on whether the project team pursues Branch A (Platform + UI) or Branch B (Rosetta Translator). 

#### Branch A: Platform for Pipeline Execution, Monitoring, and Visualization 

**Persona 1**: Clinician / Physician
* Role Description: A fetal medicine specialist who interprets brain MRIs and needs fast, clear, clinically useful imaging results without technical setup.


Key characteristics:
* Skilled in medicine, not Linux pipelines
* Time-constrained, needs results integrated into hospital imaging systems
* Prefers visual overlays and cortical thickness measurements


Responsibilities:
* Review processed MRI results and segmentations 
* Use data in patient assessments and decisions
* Provide feedback on the clarity and accuracy of outputs 

**Persona 2**: Researcher Scientist
* Role Description: A neuroscientist researcher analyzing MRI scans to study brain development using FreeSurfer and related tools.

Key characteristics:
* Comfortable with Linux and research pipelines
* Seeks reproducible results across large datasets
* Limited by local computing resources

Responsibilities: 
* Run and validate segmentation workflows 
*Export results for statistical analysis 
*Publish findings based on processed imaging data

#### Branch B: “Rosetta” Translator for Pipeline 

**Persona 1**: Research Scientist
* Role Description: A researcher who designs and runs MRI analysis pipelines, but needs portability across systems with varying compute environments (e.g., SLURM, YAML, Argo Workflow, or ChRIS), especially when the system does not natively support Tekton.

Key characteristics:
* Familiar with Tekton, SLURM, and Argo
* Prioritizes reproducibility and interoperability
* Collaborates with multi-institutional teams

Responsibilities: 
* Convert the Tekton pipeline into SLURM sbatch 
* Share workflows with collaborators in other environments 
* Validate that the results are consistent across platforms 

**Persona 2**: Research Developer
* Role Description: An academic researcher and/or startup software developer who aims to disseminate and/or commercialize their software pipelines.

Key characteristics:
* Image processing software developer
* Non-expert of cloud nor HPC

Responsibilities:
* Package their software so that it can be used in a variety of target environments, including HPC and Kubernetes

### 3. Scope and Features Of The Project
The scope of this project is to demonstrate how neuroimaging pipelines can be executed in a cloud-native pipeline using Tekton on OpenShift. The team will focus first on achieving the minimum goal of successfully running a neuroimaging workflow end-to-end, then extend the work by pursuing either **Branch A** (user-facing platform) or **Branch B** (pipeline translation tool). 

The main features that included in this project are:
* Developing lightweight utility containers that handle essential workflow tasks.
* Using Tekton to orchestrate the neuroimaging workflow.
* Running the pipeline on OpenShift.
* Testing the pipeline on a sample MRI dataset to make sure the outputs are correct and the workflow behaves as expected.
* Writing clear documentation and instructions for running the pipeline.

#### Possible Extensions:
**Branch A**: Platform for Pipeline Execution, Monitoring, and Visualization
* User-friendly interface for triggering pipeline runs.
* Real-time monitoring of pipeline status and progress.

**Branch B**: “Rosetta” Translator for Pipeline 
* A translator program that converts Tekton pipeline into formats like SLURM or Argo.
* Validation of at least one translated pipeline to confirm correctness and compatibility.

Certain elements are out of scope for this project, such as building a full library of all possible neuroimaging tools, developing advanced data management systems for long-term storage, and optimizing performance for large-scale clinical use.

### 4. Solution Concept

**Global Architectural Structure of the Project:**
The project architecture centers on containerized neuroimaging workflows deployed in Red Hat OpenShift and orchestrated with Tekton pipelines. 
[IMAGE HERE]

At the high level, the architecture includes the following components:

1. **Data Ingestion (PACS)**: Imaging data is retrieved from a clinical image database (e.g., PACS) deployed inside OpenShift.
2. **Preprocessing**: The pipeline performs standard image preparation steps to ensure data is ready for analysis.
3. **Analysis**: Containerized neuroimaging tools execute the analysis (e.g., segmentation, measurement, or other workflows).
4. **Result Export**: Processed data, derived imaging outputs, and reports are pushed back into the clinical database, making them accessible for clinicians and researchers.
5. **Pipeline Orchestration (Tekton)**: Tekton defines and automates the execution of each stage, ensuring reproducibility and consistency across runs.
6. **Monitoring and Logging**: OpenShift and Tekton provide job monitoring, error logging, and reproducibility verification.

If the team pursues **Branch A**, a web interface will be added to trigger pipelines and visualize results. If the team pursues **Branch B**, a translator will be built to export Tekton pipeline definitions into formats such as Argo, SLURM batch scripts, or ChRIS YAML, enabling use across multiple environments.

#### Design Implications and Discussion 
* **Containerization**: Packaging software such as FreeSurfer and preprocessing steps in containers ensures portability and computational reproducibility. This avoids dependency conflicts and allows the same pipeline to run consistently across diverse environments, from research clusters to cloud platforms.
* **Tekton Pipelines**: Using Tekton allows the team to represent complex neuroimaging workflows as DAGs. This provides modularity and automation, but more importantly, it improves interoperability in a domain where most workflows are ad hoc and non-standardized. Tektok’s cloud-native standards make pipelines easier to share, adapt, and integrate across teams and institutions, which is particularly valuable in neuroimaging where workflows are often highly specialized and fragmented.
* **PACS Integration**: The solution is designed to interface with PACS (Picture Archiving and Communication System), the DICOM (Digital Imaging and Communications in Medicine) standard widely used in hospitals worldwide. Orthanc can serve as an open-source reference implementation, but the integration approach remains flexible to support other PACS systems, further strengthening interoperability with clinical environments.
* **Branch Choice**:
  * Branch A emphasizes usability and accessibility for clinicians and researchers. This requires additional work in UI/UX design and visualization, making pipeline execution and monitoring more approachable.
  * Branch B emphasizes portability across diverse compute environments (e.g., SLURM HPC clusters). This requires translation logic and validation to ensure that equivalent outputs can be produced across platforms.
* **Scalability and Computational Reproducibility**: Running on OpenShift with Tekton provides elastic compute for institutions and ensures pipelines can be re-run in consistent environments, a critical requirement for research validity.
* **Limitations**: The project will not deliver production-ready EMR integration or advanced security features, as the focus is on demonstrating feasibility and workflow integration.

### 5. Acceptance Criteria
Our minimum goal (due mid-October) is to demonstrate execution of neuroimaging research software on OpenShift using Tekton Pipelines:
* Orthanc (open-source medical imaging database) is successfully deployed on OpenShift with MRI data being retrieved and passed to the pipeline.
* A user can upload or access MRI data within the OpenShift environment.
* A neuroimaging analysis pipeline (e.g., FreeSurfer) can be executed in OpenShift and completed without errors.
* Running the pipeline produces correct and verifiable outputs (e.g., processed images, segmentation maps, log files).
* Pipeline execution is automated through Tekton, so the user can trigger analysis with a single command or button.

From this point, our client provided two possible branches. Our client is also open to a team-defined continuation for which our group defines our own direction for this project.

**Branch A - User Platform Execution and Visualization**
* A user (researcher or clinician) can trigger a pipeline execution through an intuitive user interface (not only via CLI).
* The interface reports real-time feedback on pipeline status (e.g., pending, running, completed, failed).
* A user can access the pipeline outputs directly through the interface (logs, downloadable files, or basic visualization).
* Develop comprehensive onboarding documentation so that a new user can deploy and use the interface without prior system knowledge.

**Branch B - Rosetta Program for Pipeline Translation**
* A user can input a valid Tekton pipeline definition and receive an equivalent definition in at least one alternate workflow language (e.g., Argo, SLURM, or ChRIS YAML).
* The translated pipeline is syntactically valid and recognized by the target workflow system.
* At least one example Tekton pipeline from this project has been successfully translated and verified to run (or at least validate) in the target system.
* Instructions for running the translator are available and understandable by new users without prior knowledge of Tekton or the target system.

### 6. Release Planning
This project will be delivered incrementally over a series of sprints, each sprint will be building toward the overall goal: enabling neuroscience research pipelines to run reproducibly on cloud-native infrastructure (OpenShift + Tekton).

Each sprint produces a working release with demonstrable functionality, allowing for feedback, course correction, and alignment with mentor expectations.

### Release Calendar

| Sprint | Dates           | Goal / Deliverable                                                                                   |
|--------|-----------------|------------------------------------------------------------------------------------------------------|
| 0      | Sept 17 – Oct 6 | - Setup + onboarding (NERC account, repo, comms with mentor) <br> - Deploy Orthanc on OpenShift (Oct 1) |
| 1      | Oct 7 – Oct 22  | - Run a scientific MRI pipeline manually (Oct 8) <br> - Automate pipeline execution with Tekton on OpenShift (Oct 22) |
| 2      | Oct 23 – Nov 5  | - Minimum goal fully achieved: reproducible end-to-end pipeline run on OpenShift / Tekton <br> - Decide Branch A, Branch B, or group-defined Branch |
| 3      | Nov 6 – Nov 19  | **Branch Development:** <br> - Branch A → build interface for pipeline execution and monitoring <br> - Branch B → implement Tekton to Argo/SLURM/ChRIS translation prototype <br> - Branch C → TBD |
| 4      | Nov 20 – Dec 3  | - Extend chosen branch: usability improvements, add outputs/visualizations, test with additional pipelines |
| 5      | Dec 4 – Dec 10  | - Final polish: documentation, final demonstration preparation, GitHub cleanup, reproducibility check <br> - Deliver final presentation |



