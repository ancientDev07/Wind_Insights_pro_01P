import {
    getProjects
}
from "../services/project.service.js";

const projectGrid=
    document.getElementById(
        "projectGrid"
    );

export async function initializeHomePage(){

    await loadProjects();
}

async function loadProjects(){

    try{

        const projects=
            await getProjects();

        renderProjects(
            projects
        );
    }
    catch(error){

        console.error(error);
    }
}

function renderProjects(
    projects
){

    projectGrid.innerHTML="";

    if(!projects.length){

        projectGrid.innerHTML=
        `
        <div class="empty-state">

            No Projects Found

        </div>
        `;

        return;
    }

    projects.forEach(
        project=>{

            const card=
                document.createElement(
                    "div"
                );

            card.className=
                "project-card";

            card.innerHTML=
            `
            <h3>${project.name}</h3>
            <p>
                ${
                    project.description ||
                    ""
                }
            </p>
            `;

            card.addEventListener(
                "click",
                ()=>{

                    localStorage.setItem(
                        "selectedProjectId",
                        project.id
                    );

                    window.location.href=
                        "project.html";
                }
            );

            projectGrid.appendChild(
                card
            );
        }
    );
}