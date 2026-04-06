def to_int(value):
    if value is None:
        return None
    if isinstance(value, str):
        return int(value.replace(",", "").strip())
    return int(value)


def to_float(value):
    if value is None:
        return None
    if isinstance(value, str):
        return float(value.replace("%", "").strip())
    return float(value)


def insert_resultados_generales(
    conn, id_eleccion, id_group_eleccion, id_location_req, data_general
):
    conn.execute(
        """
        INSERT INTO resultados_generales (
            id_eleccion,
            id_location_req,
            id_group_eleccion,
            num_votos_emitidos,
            num_electores,
            num_percent_part,
            num_percent_ausen,
            txt_pregunta
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            id_eleccion,
            id_location_req,
            id_group_eleccion,
            to_int(data_general.get("NuVotosEmi")),
            to_int(data_general.get("NuElectores")),
            to_float(data_general.get("NuPorcPart")),
            to_float(data_general.get("NuPorcAusen")),
            data_general.get("TxPregunta"),
        ),
    )


def insert_resultados_org_politica(
    conn, id_eleccion, id_group_eleccion, id_location_req, resultados
):
    sql = """
    INSERT INTO resultados_by_org_politica (
        id_eleccion,
        id_location_req,
        id_group_eleccion,
        id_expediente,
        id_localidad,
        id_org_politica,
        name_org_politica,
        url_org_politica,
        url_ruta_plan_gobierno,
        url_symbol,
        num_votos,
        num_porc,
        url_archivo_plan_gob,
        method_http,
        tipo_link_plan
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for r in resultados:
        conn.execute(
            sql,
            (
                id_eleccion,
                id_location_req,
                id_group_eleccion,
                r.get("IdExpediente"),
                r.get("IdLocalidad"),
                r.get("IdOrgPol"),
                r.get("TxOrgPol"),
                r.get("TxRutaOrgPol"),
                r.get("TxRutaPlanGob"),
                r.get("TxRutaSimbolo"),
                to_int(r.get("NuOrgVotos")),
                to_float(r.get("NuOrgPorc")),
                r.get("TxArchivoPlanGob"),
                r.get("TxMetodoHttp"),
                r.get("TxTipoLink"),
            ),
        )


def marcar_procesado_proc_electoral(
    conn, id_eleccion, id_group_eleccion, id_location_req
):
    conn.execute(
        """
        UPDATE procesos_electorales_locations
        SET procesado = 1
        WHERE id_eleccion = ?
          AND id_group_eleccion = ?
          AND id_location_req = ?
        """,
        (id_eleccion, id_group_eleccion, id_location_req),
    )


def procesar_respuesta(conn, row, response_json):
    if response_json.get("Estado") != "success":
        raise ValueError("Respuesta no exitosa")

    data = response_json["Data"]

    with conn:  # ← transacción SQLite
        insert_resultados_generales(
            conn,
            row["id_eleccion"],
            row["id_group_eleccion"],
            row["id_location_req"],
            data["DatosGenerales"],
        )

        insert_resultados_org_politica(
            conn,
            row["id_eleccion"],
            row["id_group_eleccion"],
            row["id_location_req"],
            data["Resultados"],
        )

        marcar_procesado_proc_electoral(
            conn,
            row["id_eleccion"],
            row["id_group_eleccion"],
            row["id_location_req"],
        )
