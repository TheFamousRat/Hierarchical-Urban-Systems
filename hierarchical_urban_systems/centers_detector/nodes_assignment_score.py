from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.preprocessing import normalize  # type: ignore[import-untyped]
import scipy.sparse as sp  # type: ignore[import-untyped]

from hierarchical_urban_systems.alias import (
    FlowMatrix,
)


@dataclass(frozen=True)
class NodesAssignmentScore:
    proposed_score: float
    all_nodes_together_score: float | None = None
    all_nodes_alone_score: float | None = None

    @classmethod
    def get_exhaustivity_score_for_assignment(
        cls, flows_matrix: FlowMatrix, assignment: np.ndarray
    ) -> NodesAssignmentScore:
        """
        Returns an exhaustivity score for a given node assignment, based on the flow matrix of these nodes.
        The extreme scores, eg all nodes together or all nodes their own centers are also computed for reference.

         - Score computation

        Let A be the assignment matrix, with each row corresponding to a node. A single 1 is present in each row,
        in the column corresponding to the node center of the row's node. The rest of the row is filled with zeros.

        We then define the center matrix C, as C = A @ A.T.
        For each row, C contains a one if the row's and the column's node are in the same center, and zeros otherwise.

        F is the flow matrix, and N contains the l2-normalized flows.

        The score is then computed as:

        center_flows = C.multiply(C @ F)
        affinity_to_assigned_centers = ( #Row-wise dot product, gives similarity between a node and its center
            N.multiply(normalize(center_flows, axis=1, norm="l2")).sum(axis=1).A[:, 0]
        )
        node_flows_in_assigned_centers = C.multiply(F).sum(axis=1).A[:, 0] #Amplitude of node flows represented in a center
        total_representations = np.dot(
            similarities_to_assigned_centers,
            node_flows_in_assigned_centers,
        )
        proposal_score = total_representations / F.sum()


        """
        full_representation = flows_matrix.sum()

        norm_flows = normalize(flows_matrix, axis=1, norm="l2")

        # Score with every node its own center
        lone_centers_representation = norm_flows.diagonal() @ flows_matrix.diagonal()
        lone_centers_score = lone_centers_representation / full_representation

        # Score with every node in the same center
        merged_centers_representation = (
            norm_flows @ normalize(flows_matrix.sum(axis=0).A, axis=1, norm="l2").T
        )[:, 0] @ flows_matrix.sum(axis=1).A[:, 0]
        merged_centers_score = merged_centers_representation / full_representation

        # Below is fast, but might be dangerous memory-wise if few centers are found
        A = sp.csr_matrix(
            (np.ones_like(assignment), (np.arange(len(assignment)), assignment)),
            shape=flows_matrix.shape,
            dtype=bool,
        )
        C = A @ A.T
        similarities_to_assigned_centers = (
            norm_flows.multiply(
                normalize(C.multiply(C @ flows_matrix), axis=1, norm="l2")
            )
            .sum(axis=1)
            .A[:, 0]
        )
        node_flows_in_assigned_centers = C.multiply(flows_matrix).sum(axis=1).A[:, 0]
        total_representations = np.dot(
            similarities_to_assigned_centers,
            node_flows_in_assigned_centers,
        )
        proposal_score = total_representations / full_representation
        # Below is slow but consumes less memory
        # total_representations = 0.0
        # for node_center_idx in tqdm.tqdm(
        #     np.unique(assignment), desc="Center scores computed", ncols=TQDM_COLS_COUNT
        # ):
        #     node_members_idx = np.where(assignment == node_center_idx)[0]
        #     center_members_flows = flows_matrix[
        #         np.ix_(node_members_idx, node_members_idx)
        #     ]

        #     center_flows = center_members_flows.sum(axis=0).A[0, :]
        #     nodes_affinity_to_center = norm_flows[
        #         np.ix_(node_members_idx, node_members_idx)
        #     ] @ normalize(center_flows[:, None], axis=0, norm="l2")
        #     flows_representation_this_center = center_members_flows.multiply(
        #         nodes_affinity_to_center
        #     ).sum()
        #     total_representations += (
        #         flows_representation_this_center / full_representation
        #     )
        # proposal_score = total_representations

        return NodesAssignmentScore(
            proposed_score=proposal_score,
            all_nodes_alone_score=lone_centers_score,
            all_nodes_together_score=merged_centers_score,
        )

    def __str__(self) -> str:
        display_str = f"\033[1m{self.proposed_score * 100.0:.4f}%\033[0m"

        special_score_strings: list[str] = []
        if self.all_nodes_together_score is not None:
            special_score_strings.append(
                f"one center score: {self.all_nodes_together_score * 100.0:.4f}%"
            )
        if self.all_nodes_alone_score is not None:
            special_score_strings.append(
                f"all nodes alone score: {self.all_nodes_alone_score * 100.0:.4f}%"
            )

        if len(special_score_strings) > 0:
            display_str += f" ({', '.join(special_score_strings)})"

        return display_str
