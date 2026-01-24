document.getElementById("uploadForm").onsubmit = async (e) => {
  e.preventDefault();

  const formData = new FormData(e.target);

  const res = await fetch("/predict", {
    method: "POST",
    body: formData
  });

  const data = await res.json();

  const tbody = document.querySelector("#resultTable tbody");
  tbody.innerHTML = "";

  data.forEach(row => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${row.timestamp}</td>
      <td>${row.point_1 ? "✔" : "✘"}</td>
      <td>${row.point_2 ? "✔" : "✘"}</td>
      <td>${row.point_3 ? "✔" : "✘"}</td>
      <td>${row.person_count}</td>
    `;

    tbody.appendChild(tr);
  });
};
