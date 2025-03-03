# Domains & Converters Collection

This repository is part of a larger collection of projects focused on domain modeling, problem generation, and format conversion. The goal is to fix and enhance broken domains in PDDL, create new problem instances, and build converter scripts and other tools to work with these domains. In addition, complementary repositories (e.g., in Rust) will use the generated JSON formats for further processing.

## Overview

- **Domain Fixes:**  
  We take broken or incomplete domain definitions (in PDDL) and fix them to meet our planning needs.

- **Problem Generation:**  
  We create new problem instances in PDDL. For example, for the Zenotravel domain, 20 new problem files have been created, each representing a different scenario.

- **Format Converters:**  
  Python scripts are provided to convert PDDL files into a JSON state representationץ

- **Rust Integration:**  
  In a separate repository, Rust code is being developed to consume these JSON files. The Rust project’s data structures match the JSON format exactly, allowing for further planning, simulation, or analysis.


## Future Work
- Expand the collection to include more domains and problem sets.
- Develop additional converters for different formats.
- Enhance the Rust project to provide more advanced planning and simulation features.
  
## Contributions
Contributions, bug reports, and feature requests are welcome. Feel free to open issues or submit pull requests.
